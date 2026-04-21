import pytest
import numpy as np


@pytest.fixture
def unit_circle():
    from chalk.shapes import Circle
    return Circle(radius=1.0)


@pytest.fixture
def unit_square():
    from chalk.shapes import Square
    return Square(side=2.0)
