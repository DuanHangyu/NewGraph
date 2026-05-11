"""
API路由模块
"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
classroom_bp = Blueprint('classroom', __name__)
hint_bp = Blueprint('hint', __name__)
qa_bp = Blueprint('qa', __name__)
data_bp = Blueprint('data', __name__)

from . import graph  # noqa: E402, F401
from . import classroom  # noqa: E402, F401
from . import hint  # noqa: E402, F401
from . import qa  # noqa: E402, F401
from . import data  # noqa: E402, F401
