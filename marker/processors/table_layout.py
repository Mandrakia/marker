from typing import Annotated, List, Tuple

from marker.processors import BaseProcessor
from marker.schema import BlockTypes
from marker.schema.blocks import TableCell
from marker.schema.document import Document
from marker.schema.registry import get_block_class


class TableLayoutProcessor(BaseProcessor):
    """Convert tables used for formatting text into standard blocks."""

    block_types: Annotated[Tuple[BlockTypes], "Block types to process."] = (BlockTypes.Table,)
    max_cell_text_length: Annotated[
        int,
        "Average cell text length threshold to treat as a formatting table.",
    ] = 40

    def is_formatting_table(self, cells: List[TableCell]) -> bool:
        if not cells:
            return False
        row_count = len({c.row_id for c in cells})
        col_count = len({c.col_id for c in cells})
        avg_len = sum(len(" ".join(c.text_lines or [])) for c in cells) / len(cells)
        if row_count == 1 or col_count == 1:
            return True
        if row_count <= 2 and col_count <= 2 and avg_len > self.max_cell_text_length:
            return True
        return False

    def __call__(self, document: Document):
        SectionHeader = get_block_class(BlockTypes.SectionHeader)
        Text = get_block_class(BlockTypes.Text)
        ListGroup = get_block_class(BlockTypes.ListGroup)
        ListItem = get_block_class(BlockTypes.ListItem)

        for page in document.pages:
            for block in page.contained_blocks(document, self.block_types):
                cells: List[TableCell] = block.contained_blocks(document, (BlockTypes.TableCell,))
                if not self.is_formatting_table(cells):
                    continue

                idx = page.structure.index(block.id)
                page.structure.remove(block.id)
                block.ignore_for_output = True

                row_count = len({c.row_id for c in cells})
                col_count = len({c.col_id for c in cells})

                if col_count == 1:
                    list_group = page.add_full_block(
                        ListGroup(polygon=block.polygon, page_id=page.page_id)
                    )
                    for cell in sorted(cells, key=lambda c: (c.row_id, c.col_id)):
                        text = " ".join(cell.text_lines or [])
                        li = page.add_full_block(
                            ListItem(
                                polygon=cell.polygon,
                                page_id=cell.page_id,
                                html=text,
                            )
                        )
                        list_group.add_structure(li)
                    page.structure.insert(idx, list_group.id)
                else:
                    first_row = min(c.row_id for c in cells)
                    header_cells = [c for c in cells if c.row_id == first_row]
                    header_text = " ".join(
                        " ".join(c.text_lines or []) for c in header_cells
                    ).strip()
                    header = page.add_full_block(
                        SectionHeader(
                            polygon=header_cells[0].polygon,
                            page_id=page.page_id,
                            html=header_text,
                        )
                    )
                    page.structure.insert(idx, header.id)

                    remaining = [c for c in cells if c.row_id != first_row]
                    if remaining:
                        text = " ".join(
                            " ".join(c.text_lines or []) for c in remaining
                        ).strip()
                        text_block = page.add_full_block(
                            Text(
                                polygon=block.polygon,
                                page_id=page.page_id,
                                html=text,
                            )
                        )
                        page.structure.insert(idx + 1, text_block.id)
