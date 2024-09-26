pub mod errors;
pub mod lexer;
pub mod markup;
pub mod query;

use errors::LiquidError;
use markup::Markup;
use pyo3::prelude::*;
use query::Query;

// TODO: pymethods

#[pyfunction]
fn tokenize(source: &str) -> Result<Vec<Markup>, LiquidError> {
    lexer::Lexer::new().tokenize(source)
}

#[pyfunction]
fn parse_query(path: &str) -> Result<Query, LiquidError> {
    lexer::Lexer::new().parse_query(path)
}

#[pyfunction]
fn dump(source: &str) {
    lexer::Lexer::new().dump(source);
}

/// A Python module implemented in Rust.
#[pymodule]
fn _liquid2(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add(
        "PyLiquidError",
        m.py().get_type_bound::<errors::PyLiquidError>(),
    )?;
    m.add(
        "LiquidTypeError",
        m.py().get_type_bound::<errors::LiquidTypeError>(),
    )?;
    m.add(
        "LiquidSyntaxError",
        m.py().get_type_bound::<errors::LiquidSyntaxError>(),
    )?;
    m.add(
        "LiquidNameError",
        m.py().get_type_bound::<errors::LiquidNameError>(),
    )?;
    m.add(
        "LiquidExtensionError",
        m.py().get_type_bound::<errors::LiquidExtensionError>(),
    )?;
    m.add_function(wrap_pyfunction!(dump, m)?)?;
    m.add_function(wrap_pyfunction!(tokenize, m)?)?;
    m.add_function(wrap_pyfunction!(parse_query, m)?)?;
    m.add_class::<query::Segment>()?;
    m.add_class::<query::Selector>()?;
    m.add_class::<query::ComparisonOperator>()?;
    m.add_class::<markup::Markup>()?;
    m.add_class::<markup::Token>()?;
    m.add_class::<markup::RangeArgument>()?;
    m.add_class::<markup::Whitespace>()?;
    Ok(())
}
