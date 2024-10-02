//! JSONPath query syntax tree
//!

use std::fmt::{self, Write};

use pyo3::prelude::*;

#[pyclass]
#[derive(Debug, Clone)]
pub struct Query {
    #[pyo3(get)]
    pub segments: Vec<Segment>,
}

impl Query {
    // Returns `true` if this query has no segments, or `false` otherwise.
    pub fn is_empty(&self) -> bool {
        self.segments.is_empty()
    }

    // Returns `true` if this query can resolve to at most one node, or `false` otherwise.
    pub fn is_singular(&self) -> bool {
        self.segments.iter().all(|segment| {
            if let Segment::Child { selectors, .. } = segment {
                return selectors.len() == 1
                    && selectors.first().is_some_and(|selector| {
                        matches!(selector, Selector::Name { .. } | Selector::Index { .. })
                    });
            }
            false
        })
    }
}

#[pymethods]
impl Query {
    pub fn as_word(&self) -> Option<String> {
        if self.segments.len() != 1 {
            return None;
        }

        if let Some(Segment::Child { selectors, .. }) = self.segments.get(0) {
            if selectors.len() != 1 {
                return None;
            }

            if let Some(Selector::Name { name, .. }) = selectors.get(0) {
                Some(name.to_owned())
            } else {
                None
            }
        } else {
            None
        }
    }
}

impl fmt::Display for Query {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "${}",
            self.segments
                .iter()
                .map(|s| s.to_string())
                .collect::<Vec<String>>()
                .join("")
        )
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum Segment {
    Child {
        selectors: Vec<Selector>,
        line_col: (usize, usize),
    },
    Recursive {
        selectors: Vec<Selector>,
        line_col: (usize, usize),
    },
    Eoi {}, // Is this needed?
}

impl fmt::Display for Segment {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Segment::Child { selectors, .. } => {
                write!(
                    f,
                    "[{}]",
                    selectors
                        .iter()
                        .map(|s| s.to_string())
                        .collect::<Vec<String>>()
                        .join(", ")
                )
            }
            Segment::Recursive { selectors, .. } => {
                write!(
                    f,
                    "..[{}]",
                    selectors
                        .iter()
                        .map(|s| s.to_string())
                        .collect::<Vec<String>>()
                        .join(", ")
                )
            }
            Segment::Eoi {} => Ok(()),
        }
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum Selector {
    Name {
        name: String,
        line_col: (usize, usize),
    },
    Index {
        index: i64,
        line_col: (usize, usize),
    },
    Slice {
        start: Option<i64>,
        stop: Option<i64>,
        step: Option<i64>,
        line_col: (usize, usize),
    },
    Wild {
        line_col: (usize, usize),
    },
    Filter {
        expression: Box<FilterExpression>,
        line_col: (usize, usize),
    },
    SingularQuery {
        query: Box<Query>,
        line_col: (usize, usize),
    },
}

impl fmt::Display for Selector {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Selector::Name { name, .. } => write!(f, "'{name}'"),
            Selector::Index {
                index: array_index, ..
            } => write!(f, "{array_index}"),
            Selector::Slice {
                start, stop, step, ..
            } => {
                write!(
                    f,
                    "{}:{}:{}",
                    start
                        .and_then(|i| Some(i.to_string()))
                        .unwrap_or(String::from("")),
                    stop.and_then(|i| Some(i.to_string()))
                        .unwrap_or(String::from("")),
                    step.and_then(|i| Some(i.to_string()))
                        .unwrap_or(String::from("1")),
                )
            }
            Selector::Wild { .. } => f.write_char('*'),
            Selector::Filter { expression, .. } => write!(f, "?{expression}"),
            Selector::SingularQuery { query, .. } => write!(f, "{query}"),
        }
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum FilterExpression {
    True_ {
        line_col: (usize, usize),
    },
    False_ {
        line_col: (usize, usize),
    },
    Null {
        line_col: (usize, usize),
    },
    StringLiteral {
        value: String,
        line_col: (usize, usize),
    },
    Int {
        value: i64,
        line_col: (usize, usize),
    },
    Float {
        value: f64,
        line_col: (usize, usize),
    },
    Not {
        expression: Box<FilterExpression>,
        line_col: (usize, usize),
    },
    Logical {
        left: Box<FilterExpression>,
        operator: LogicalOperator,
        right: Box<FilterExpression>,
        line_col: (usize, usize),
    },
    Comparison {
        left: Box<FilterExpression>,
        operator: ComparisonOperator,
        right: Box<FilterExpression>,
        line_col: (usize, usize),
    },
    RelativeQuery {
        query: Box<Query>,
        line_col: (usize, usize),
    },
    RootQuery {
        query: Box<Query>,
        line_col: (usize, usize),
    },
    Function {
        name: String,
        args: Vec<FilterExpression>,
        line_col: (usize, usize),
    },
}

impl FilterExpression {
    pub fn is_literal(&self) -> bool {
        matches!(
            self,
            FilterExpression::True_ { .. }
                | FilterExpression::False_ { .. }
                | FilterExpression::Null { .. }
                | FilterExpression::StringLiteral { .. }
                | FilterExpression::Int { .. }
                | FilterExpression::Float { .. }
        )
    }
}

impl fmt::Display for FilterExpression {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use FilterExpression::*;
        match self {
            True_ { .. } => f.write_str("true"),
            False_ { .. } => f.write_str("false"),
            Null { .. } => f.write_str("null"),
            StringLiteral { value, .. } => write!(f, "\"{value}\""),
            Int { value, .. } => write!(f, "{value}"),
            Float { value, .. } => write!(f, "{value}"),
            Not { expression, .. } => write!(f, "!{expression}"),
            Logical {
                left,
                operator,
                right,
                ..
            } => write!(f, "({left} {operator} {right})"),
            Comparison {
                left,
                operator,
                right,
                ..
            } => write!(f, "{left} {operator} {right}"),
            RelativeQuery { query, .. } => {
                write!(
                    f,
                    "@{}",
                    query
                        .segments
                        .iter()
                        .map(|s| s.to_string())
                        .collect::<Vec<String>>()
                        .join("")
                )
            }
            RootQuery { query, .. } => {
                write!(
                    f,
                    "${}",
                    query
                        .segments
                        .iter()
                        .map(|s| s.to_string())
                        .collect::<Vec<String>>()
                        .join("")
                )
            }
            Function { name, args, .. } => {
                write!(
                    f,
                    "{}({})",
                    name,
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<String>>()
                        .join(", ")
                )
            }
        }
    }
}

#[pyclass(eq, eq_int)]
#[derive(Debug, Clone, PartialEq)]
pub enum LogicalOperator {
    And,
    Or,
}

impl fmt::Display for LogicalOperator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LogicalOperator::And => f.write_str("&&"),
            LogicalOperator::Or => f.write_str("||"),
        }
    }
}

#[pymethods]
impl LogicalOperator {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass(eq, eq_int)]
#[derive(Debug, Clone, PartialEq)]
pub enum ComparisonOperator {
    Eq,
    Ne,
    Ge,
    Gt,
    Le,
    Lt,
}

impl fmt::Display for ComparisonOperator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ComparisonOperator::Eq => f.write_str("=="),
            ComparisonOperator::Ne => f.write_str("!="),
            ComparisonOperator::Ge => f.write_str(">="),
            ComparisonOperator::Gt => f.write_str(">"),
            ComparisonOperator::Le => f.write_str("<="),
            ComparisonOperator::Lt => f.write_str("<"),
        }
    }
}

#[pymethods]
impl ComparisonOperator {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

impl<'py> pyo3::FromPyObject<'py> for Box<Query> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        ob.extract::<Query>().map(Box::new)
    }
}

impl pyo3::IntoPy<pyo3::PyObject> for Box<Query> {
    fn into_py(self, py: pyo3::Python<'_>) -> pyo3::PyObject {
        (*self).into_py(py)
    }
}

impl<'py> pyo3::FromPyObject<'py> for Box<FilterExpression> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        ob.extract::<FilterExpression>().map(Box::new)
    }
}

impl pyo3::IntoPy<pyo3::PyObject> for Box<FilterExpression> {
    fn into_py(self, py: pyo3::Python<'_>) -> pyo3::PyObject {
        (*self).into_py(py)
    }
}
