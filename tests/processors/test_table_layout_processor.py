import pytest

from marker.processors.table_layout import TableLayoutProcessor
from marker.schema import BlockTypes
from marker.schema.blocks import Table, TableCell
from marker.schema.groups.page import PageGroup
from marker.schema.polygon import PolygonBox
from marker.schema.document import Document


def make_polygon(x1, y1, x2, y2):
    return PolygonBox(polygon=[[x1, y1], [x2, y1], [x2, y2], [x1, y2]])


def test_table_layout_processor_list():
    page = PageGroup(polygon=make_polygon(0, 0, 100, 100), page_id=0, children=[], structure=[])
    table = Table(polygon=make_polygon(10, 10, 90, 90), page_id=0, structure=[])
    page.add_full_block(table)
    page.structure.append(table.id)

    for i, text in enumerate(["A", "B", "C"]):
        cell = TableCell(
            polygon=make_polygon(10, 10 + i * 10, 90, 20 + i * 10),
            text_lines=[text],
            rowspan=1,
            colspan=1,
            row_id=i,
            col_id=0,
            is_header=False,
            page_id=0,
        )
        page.add_full_block(cell)
        table.add_structure(cell)

    document = Document(filepath="", pages=[page])
    processor = TableLayoutProcessor({})
    processor(document)

    list_groups = page.contained_blocks(document, (BlockTypes.ListGroup,))
    assert len(list_groups) == 1
    list_items = list_groups[0].contained_blocks(document, (BlockTypes.ListItem,))
    assert len(list_items) == 3
    assert table.ignore_for_output

