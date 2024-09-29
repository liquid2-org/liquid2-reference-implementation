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
        hashes: String,
        text: String,
    },
    Output {
        span: (usize, usize),
        wc: (Whitespace, Whitespace),
        expression: Vec<Token>,
    },
    Tag {
        span: (usize, usize),
        wc: (Whitespace, Whitespace),
        name: String,
        expression: Option<Vec<Token>>,
    },
    EOI {},
}

impl fmt::Display for Markup {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Markup::Content { text, .. } => f.write_str(text),
            Markup::Raw { wc, text, .. } => write!(
                f,
                "{{%{} raw {}%}}{}{{%{} endraw {}%}}",
                wc.0, wc.1, text, wc.2, wc.3
            ),
            Markup::Comment {
                wc, hashes, text, ..
            } => {
                write!(f, "{{{}{}{}{}{}}}", hashes, wc.0, text, wc.1, hashes)
            }
            Markup::Output { wc, expression, .. } => {
                let expr = expression
                    .into_iter()
                    .map(|e| e.to_string())
                    .collect::<Vec<String>>()
                    .join("");
                write!(f, "{{{{{} {} {}}}}}", wc.0, expr, wc.1)
            }
            Markup::Tag {
                wc,
                name,
                expression,
                ..
            } => {
                if let Some(expr) = expression {
                    if expr.is_empty() {
                        write!(f, "{{%{} {} {}%}}", wc.0, name, wc.1)
                    } else {
                        // TODO: Smarter join. No space after some symbols
                        let expr_ = expr
                            .into_iter()
                            .map(|e| e.to_string())
                            .collect::<Vec<String>>()
                            .join(" ");
                        write!(f, "{{%{} {} {} {}%}}", wc.0, name, expr_, wc.1)
                    }
                } else {
                    write!(f, "{{%{} {} {}%}}", wc.0, name, wc.1)
                }
            }
            Markup::EOI {} => Ok(()),
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
pub enum Token {
    True_ {
        index: usize,
    },
    False_ {
        index: usize,
    },
    And {
        index: usize,
    },
    Or {
        index: usize,
    },
    In {
        index: usize,
    },
    Not {
        index: usize,
    },
    Contains {
        index: usize,
    },
    Null {
        index: usize,
    },
    If {
        index: usize,
    },
    Else {
        index: usize,
    },
    With {
        index: usize,
    },
    As {
        index: usize,
    },
    For {
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
    Colon {
        index: usize,
    },
    Pipe {
        index: usize,
    },
    DoublePipe {
        index: usize,
    },
    Comma {
        index: usize,
    },
    LeftParen {
        index: usize,
    },
    RightParen {
        index: usize,
    },
    Assign {
        index: usize,
    },
    StringLiteral {
        index: usize,
        value: String,
    },
    IntegerLiteral {
        index: usize,
        value: i64,
    },
    FloatLiteral {
        index: usize,
        value: f64,
    },
    Word {
        index: usize,
        value: String,
    },
    RangeLiteral {
        index: usize,
        start: RangeArgument,
        stop: RangeArgument,
    },
    Query {
        index: usize,
        path: Query,
    },
}

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Token::True_ { .. } => f.write_str("true"),
            Token::False_ { .. } => f.write_str("false"),
            Token::And { .. } => f.write_str("and"),
            Token::Or { .. } => f.write_str("or"),
            Token::In { .. } => f.write_str("in"),
            Token::Not { .. } => f.write_str("not"),
            Token::Contains { .. } => f.write_str("contains"),
            Token::Null { .. } => f.write_str("null"),
            Token::If { .. } => f.write_str("if"),
            Token::Else { .. } => f.write_str("else"),
            Token::With { .. } => f.write_str("with"),
            Token::As { .. } => f.write_str("as"),
            Token::For { .. } => f.write_str("for"),
            Token::Eq { .. } => f.write_str("=="),
            Token::Ne { .. } => f.write_str("!="),
            Token::Ge { .. } => f.write_str(">="),
            Token::Gt { .. } => f.write_str(">"),
            Token::Le { .. } => f.write_str("<="),
            Token::Lt { .. } => f.write_str("<"),
            Token::Colon { .. } => f.write_str(":"),
            Token::Pipe { .. } => f.write_str("|"),
            Token::DoublePipe { .. } => f.write_str("||"),
            Token::Comma { .. } => f.write_str(","),
            Token::LeftParen { .. } => f.write_str("("),
            Token::RightParen { .. } => f.write_str(")"),
            Token::Assign { .. } => f.write_str("="),
            Token::StringLiteral { value, .. } => write!(f, "'{value}'"),
            Token::IntegerLiteral { value, .. } => write!(f, "{value}"),
            Token::FloatLiteral { value, .. } => write!(f, "{value}"),
            Token::Word { value, .. } => write!(f, "{value}"),
            Token::RangeLiteral { start, stop, .. } => write!(f, "({start}..{stop})"),
            Token::Query { path, .. } => {
                if let Some(word) = path.as_word() {
                    write!(f, "{word}")
                } else {
                    write!(f, "{path}")
                }
            }
        }
    }
}

#[pymethods]
impl Token {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass(frozen)]
#[derive(Debug, Clone)]
pub enum RangeArgument {
    StringLiteral { index: usize, value: String },
    IntegerLiteral { index: usize, value: i64 },
    FloatLiteral { index: usize, value: f64 },
    Query { index: usize, path: Query },
}

impl fmt::Display for RangeArgument {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RangeArgument::StringLiteral { value, .. } => write!(f, "'{value}'"),
            RangeArgument::IntegerLiteral { value, .. } => write!(f, "{value}"),
            RangeArgument::FloatLiteral { value, .. } => write!(f, "{value}"),
            RangeArgument::Query { path, .. } => {
                if let Some(word) = path.as_word() {
                    write!(f, "{word}")
                } else {
                    write!(f, "{path}")
                }
            }
        }
    }
}

#[pymethods]
impl RangeArgument {
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
