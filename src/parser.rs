use pyo3::prelude::*;

use pest::Parser;
use pest_derive::Parser;

#[derive(Parser)]
#[grammar = "liquid2.pest"]
struct Liquid;

#[pyclass]
pub struct LiquidParser {}

#[pymethods]
impl LiquidParser {
    #[new]
    pub fn new() -> Self {
        LiquidParser {}
    }

    pub fn parse_dump(&self, template: &str) {
        let elements = Liquid::parse(Rule::liquid, template);
        println!("{:#?}", elements);
    }
}
