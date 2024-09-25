pub mod ast;
pub mod errors;
pub mod markup;
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
    m.add_function(wrap_pyfunction!(parse, m)?)?;
    m.add_class::<ast::Node>()?;
    m.add_class::<ast::BooleanExpression>()?;
    m.add_class::<ast::FilteredExpression>()?;
    m.add_class::<ast::Filter>()?;
    m.add_class::<ast::InlineCondition>()?;
    m.add_class::<ast::BooleanOperator>()?;
    m.add_class::<ast::CompareOperator>()?;
    m.add_class::<ast::MembershipOperator>()?;
    m.add_class::<ast::Primitive>()?;
    m.add_class::<ast::WhenTag>()?;
    m.add_class::<ast::ElseTag>()?;
    m.add_class::<ast::ElsifTag>()?;
    m.add_class::<ast::CommonArgument>()?;
    m.add_class::<ast::WhitespaceControl>()?;
    m.add_class::<ast::Whitespace>()?;
    m.add_class::<query::Segment>()?;
    m.add_class::<query::Selector>()?;
    m.add_class::<query::ComparisonOperator>()?;
    Ok(())
}
