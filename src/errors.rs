use std::fmt;

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;

#[derive(Debug)]
pub enum LiquidErrorType {
    LexerError,
    SyntaxError,
    TypeError,
    NameError,
    ExtError,
}

#[derive(Debug)]
pub struct LiquidError {
    pub kind: LiquidErrorType,
    pub msg: String,
}

impl LiquidError {
    pub fn new(error: LiquidErrorType, msg: String) -> Self {
        Self { kind: error, msg }
    }

    pub fn syntax(msg: String) -> Self {
        Self {
            kind: LiquidErrorType::SyntaxError,
            msg,
        }
    }

    pub fn typ(msg: String) -> Self {
        Self {
            kind: LiquidErrorType::TypeError,
            msg,
        }
    }

    pub fn name(msg: String) -> Self {
        Self {
            kind: LiquidErrorType::NameError,
            msg,
        }
    }

    pub fn ext(msg: String) -> Self {
        Self {
            kind: LiquidErrorType::ExtError,
            msg,
        }
    }
}

impl std::error::Error for LiquidError {}

create_exception!(
    jpq,
    PyLiquidError,
    PyException,
    "Base exception for all Liquid errors."
);

create_exception!(jpq, LiquidTypeError, PyLiquidError, "Liquid type error.");

create_exception!(
    jpq,
    LiquidSyntaxError,
    PyLiquidError,
    "Liquid syntax error."
);

create_exception!(jpq, LiquidNameError, PyLiquidError, "Liquid name error.");

create_exception!(
    jpq,
    LiquidExtensionError,
    PyLiquidError,
    "Liquid function extension error."
);

impl std::convert::From<LiquidError> for PyErr {
    fn from(err: LiquidError) -> Self {
        use LiquidErrorType::*;
        match err.kind {
            // TODO: improve error messages
            TypeError => LiquidTypeError::new_err(err.to_string()),
            SyntaxError => LiquidSyntaxError::new_err(err.to_string()),
            NameError => LiquidNameError::new_err(err.to_string()),
            ExtError => LiquidExtensionError::new_err(err.to_string()),
            _ => PyLiquidError::new_err(err.to_string()),
        }
    }
}

impl fmt::Display for LiquidError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.msg)
    }
}
