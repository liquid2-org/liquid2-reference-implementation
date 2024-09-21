pub mod ast;
pub mod errors;
pub mod parser;
pub mod query;

use ast::Template;
use errors::LiquidError;
use parser::LiquidParser;
use pyo3::prelude::*;

#[pyfunction]
fn dump(template: &str) {
    let parser = LiquidParser::new();
    parser.parse_dump(template);
}

#[pyfunction]
fn parse(template: &str) -> Result<Template, LiquidError> {
    let parser = LiquidParser::new();
    parser.parse(template)
}

/// A Python module implemented in Rust.
#[pymodule]
fn liquid2(m: &Bound<'_, PyModule>) -> PyResult<()> {
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
    m.add_function(wrap_pyfunction!(parse, m)?)?;
    m.add_class::<ast::Node>()?;
    Ok(())
}
