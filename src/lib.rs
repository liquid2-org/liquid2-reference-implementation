pub mod ast;
pub mod parser;
pub mod query;

use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
fn liquid2(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<parser::LiquidParser>()?;
    Ok(())
}
