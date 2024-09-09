//! Liquid template syntax tree
//!
use pyo3::prelude::*;

use crate::query::Query;

#[pyclass]
#[derive(Debug, Clone)]
pub struct Template {
    #[pyo3(get)]
    pub liquid: Vec<Node>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum Node {
    EOI {},
    Content {
        text: String,
    },
    Output {
        whitespace_control: WhitespaceControl,
        expression: FilteredExpression,
    },
    Raw {
        whitespace_control: (WhitespaceControl, WhitespaceControl),
        text: String,
    },
    Comment {
        whitespace_control: WhitespaceControl,
        text: String,
    },
    AssignTag {
        whitespace_control: WhitespaceControl,
        identifier: String,
        expression: FilteredExpression,
    },
    CaptureTag {
        whitespace_control: (WhitespaceControl, WhitespaceControl),
        identifier: String,
        block: Vec<Node>,
    },
    CaseTag {
        whitespace_control: (WhitespaceControl, WhitespaceControl),
        whens: Vec<ConditionalBlock>,
        default: Option<Vec<Node>>,
    },
    CycleTag {
        whitespace_control: WhitespaceControl,
        name: Option<String>,
        args: Vec<Primitive>,
    },
    DecrementTag {
        whitespace_control: WhitespaceControl,
        name: String,
    },
    IncrementTag {
        whitespace_control: WhitespaceControl,
        name: String,
    },
    EchoTag {
        whitespace_control: WhitespaceControl,
        expression: FilteredExpression,
    },
    ForTag {
        whitespace_control: (WhitespaceControl, WhitespaceControl),
        name: String,
        iterable: Primitive,
        limit: Primitive,
        offset: Primitive,
        reversed: bool,
        block: Vec<Node>,
    },
    BreakTag {
        whitespace_control: WhitespaceControl,
    },
    ContinueTag {
        whitespace_control: WhitespaceControl,
    },
    IfTag {
        whitespace_control: (WhitespaceControl, WhitespaceControl),
        condition: Box<ConditionalBlock>,
        alternatives: Vec<ConditionalBlock>,
        default: Option<Vec<Node>>,
    },
    UnlessTag {
        whitespace_control: (WhitespaceControl, WhitespaceControl),
        condition: Box<ConditionalBlock>,
        alternatives: Vec<ConditionalBlock>,
        default: Option<Vec<Node>>,
    },
    IncludeTag {
        whitespace_control: WhitespaceControl,
        target: Primitive,
        repeat: bool,
        variable: Primitive,
        alias: String,
        args: Vec<CommonArgument>,
    },
    RenderTag {
        whitespace_control: WhitespaceControl,
        target: Primitive,
        repeat: bool,
        variable: Primitive,
        alias: String,
        args: Vec<CommonArgument>,
    },
    LiquidTag {
        whitespace_control: WhitespaceControl,
        block: Vec<Node>,
    },
    TagExtension {
        whitespace_control: (WhitespaceControl, Option<WhitespaceControl>),
        name: String,
        args: Vec<CommonArgument>,
        block: Option<Vec<Node>>,
    },
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct FilteredExpression {
    #[pyo3(get)]
    pub left: Primitive,
    #[pyo3(get)]
    pub filters: Option<Vec<Filter>>,
    #[pyo3(get)]
    pub condition: Option<InlineCondition>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct InlineCondition {
    #[pyo3(get)]
    pub expr: Option<BooleanExpression>,
    #[pyo3(get)]
    pub alternative: Option<Primitive>,
    #[pyo3(get)]
    pub alternative_filters: Vec<Filter>,
    #[pyo3(get)]
    pub tail_filters: Vec<Filter>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct InfixExpression {
    #[pyo3(get)]
    pub left: Box<BooleanExpression>,
    #[pyo3(get)]
    pub operator: String, // TODO: or enum
    #[pyo3(get)]
    pub right: Box<BooleanExpression>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct PrefixExpression {
    #[pyo3(get)]
    pub operator: String, // TODO: or enum
    #[pyo3(get)]
    pub right: Box<BooleanExpression>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum BooleanExpression {
    Primitive { expr: Primitive },
    Prefix { expr: PrefixExpression },
    Infix { expr: InfixExpression },
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Filter {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub args: Vec<CommonArgument>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum Primitive {
    TrueLiteral {},
    FalseLiteral {},
    NullLiteral {},
    Integer { value: i64 },
    Float { value: f64 },
    StringLiteral { value: String },
    Range { start: i64, stop: i64 },
    Query { path: Query },
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ConditionalBlock {
    #[pyo3(get)]
    pub condition: BooleanExpression,
    #[pyo3(get)]
    pub block: Vec<Node>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct CommonArgument {
    #[pyo3(get)]
    pub value: Option<Primitive>,
    #[pyo3(get)]
    pub name: Option<String>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct WhitespaceControl {
    #[pyo3(get)]
    pub left: Whitespace,
    #[pyo3(get)]
    pub right: Whitespace,
}

#[pyclass(eq, eq_int)]
#[derive(Debug, Clone, PartialEq)]
pub enum Whitespace {
    Plus,
    Minus,
    Smart,
    Default,
}

impl Whitespace {
    pub fn from_str(s: &str) -> Self {
        match s {
            "+" => Self::Plus,
            "-" => Self::Minus,
            "~" => Self::Smart,
            "" => Self::Default,
            _ => unreachable!(),
        }
    }
}

impl<'py> pyo3::FromPyObject<'py> for Box<ConditionalBlock> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        ob.extract::<ConditionalBlock>().map(Box::new)
    }
}

impl pyo3::IntoPy<pyo3::PyObject> for Box<ConditionalBlock> {
    fn into_py(self, py: pyo3::Python<'_>) -> pyo3::PyObject {
        (*self).into_py(py)
    }
}

impl<'py> pyo3::FromPyObject<'py> for Box<BooleanExpression> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        ob.extract::<BooleanExpression>().map(Box::new)
    }
}

impl pyo3::IntoPy<pyo3::PyObject> for Box<BooleanExpression> {
    fn into_py(self, py: pyo3::Python<'_>) -> pyo3::PyObject {
        (*self).into_py(py)
    }
}
