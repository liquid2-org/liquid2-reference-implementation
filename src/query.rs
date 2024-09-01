//! JSONPath query syntax tree
//!

#[derive(Debug, Clone)]
pub struct Query {
    pub segments: Vec<Segment>,
}

#[derive(Debug, Clone)]
pub enum Segment {
    Child { selectors: Vec<Selector> },
    Recursive { selectors: Vec<Selector> },
    Eoi {},
}

#[derive(Debug, Clone)]
pub enum Selector {
    Name {
        name: String,
    },
    Index {
        index: i64,
    },
    Slice {
        start: Option<i64>,
        stop: Option<i64>,
        step: Option<i64>,
    },
    Wild {},
    Filter {
        expression: Box<FilterExpression>,
    },
}

#[derive(Debug, Clone)]
pub enum FilterExpression {
    True_ {},
    False_ {},
    Null {},
    StringLiteral {
        value: String,
    },
    Int {
        value: i64,
    },
    Float {
        value: f64,
    },
    Not {
        expression: Box<FilterExpression>,
    },
    Logical {
        left: Box<FilterExpression>,
        operator: LogicalOperator,
        right: Box<FilterExpression>,
    },
    Comparison {
        left: Box<FilterExpression>,
        operator: ComparisonOperator,
        right: Box<FilterExpression>,
    },
    RelativeQuery {
        query: Box<Query>,
    },
    RootQuery {
        query: Box<Query>,
    },
    Function {
        name: String,
        args: Vec<FilterExpression>,
    },
}

#[derive(Debug, Clone)]
pub enum LogicalOperator {
    And,
    Or,
}

#[derive(Debug, Clone)]
pub enum ComparisonOperator {
    Eq,
    Ne,
    Ge,
    Gt,
    Le,
    Lt,
}
