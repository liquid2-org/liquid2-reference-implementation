use pyo3::prelude::*;
use std::fmt::{self};

use crate::query::Query;

#[pyclass(frozen)]
#[derive(Debug, Clone)]
pub enum Markup {
    Content {
        span: (usize, usize),
        text: String,
    },
    Raw {
        span: (usize, usize),
        wc: (Whitespace, Whitespace, Whitespace, Whitespace),
        text: String,
    },
    Comment {
        span: (usize, usize),
        wc: (Whitespace, Whitespace),
        text: String,
    },
    Output {
        span: (usize, usize),
        wc: (Whitespace, Whitespace),
        expression: Vec<ExpressionToken>,
    },
    Tag {
        span: (usize, usize),
        wc: (Whitespace, Whitespace),
        expression: Vec<ExpressionToken>,
    },
}

impl fmt::Display for Markup {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Markup::Content { span, .. } => {
                write!(f, "Markup.Content(span=({}, {}))", span.0, span.1)
            }
            Markup::Raw { span, .. } => write!(f, "Markup.Raw(span=({}, {}))", span.0, span.1),
            Markup::Comment { span, .. } => {
                write!(f, "Markup.Comment(span=({}, {}))", span.0, span.1)
            }
            Markup::Output { span, .. } => {
                write!(f, "Markup.Output(span=({}, {}))", span.0, span.1)
            }
            Markup::Tag { span, .. } => write!(f, "Markup.Tag(span=({}, {}))", span.0, span.1),
        }
    }
}

#[pymethods]
impl Markup {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass(frozen)]
#[derive(Debug, Clone)]
pub enum ExpressionToken {
    And {
        index: usize,
    },
    Or {
        index: usize,
    },
    Eq {
        index: usize,
    },
    Ne {
        index: usize,
    },
    Ge {
        index: usize,
    },
    Gt {
        index: usize,
    },
    Le {
        index: usize,
    },
    Lt {
        index: usize,
    },
    In {
        index: usize,
    },
    Colon {
        index: usize,
    },
    Pipe {
        index: usize,
    },
    Comma {
        index: usize,
    },
    StringLiteral {
        index: usize,
        value: String,
    },
    IntegerLiteral {
        index: usize,
        value: String,
    },
    FloatLiteral {
        index: usize,
        value: String,
    },
    Name {
        index: usize,
        value: String,
    },
    RangeLiteral {
        index: usize,
        start: String,
        stop: String,
    },
    Query {
        index: usize,
        path: Query,
    },
}

impl fmt::Display for ExpressionToken {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ExpressionToken::And { index } => write!(f, "Token(index={index}, value='and')"),
            ExpressionToken::Or { index } => write!(f, "Token(index={index}, value='or')"),
            _ => todo!(),
        }
    }
}

#[pymethods]
impl ExpressionToken {
    fn __str__(&self) -> String {
        self.to_string()
    }
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
            _ => unreachable!("{:#?}", s),
        }
    }
}

impl fmt::Display for Whitespace {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Whitespace::Plus => write!(f, "+"),
            Whitespace::Minus => write!(f, "-"),
            Whitespace::Smart => write!(f, "~"),
            Whitespace::Default => Ok(()),
        }
    }
}

#[pymethods]
impl Whitespace {
    fn __str__(&self) -> String {
        self.to_string()
    }
}
