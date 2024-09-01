//! Liquid template syntax tree
//!

use crate::query::Query;

#[derive(Debug)]
pub struct Template {
    pub liquid: Vec<Node>,
}

#[derive(Debug)]
pub enum Node {
    Content {
        text: String,
    },
    Output {
        whitespace_control: WhiteSpaceControl,
        expression: FilteredExpression,
    },
    Raw {
        whitespace_control: WhiteSpaceControl,
        text: String,
    },
    Comment {
        whitespace_control: WhiteSpaceControl,
        text: String,
    },
    AssignTag {
        whitespace_control: WhiteSpaceControl,
        identifier: String,
        expression: FilteredExpression,
    },
    CaptureTag {
        whitespace_control: WhiteSpaceControl,
        identifier: String,
        block: Vec<Node>,
    },
    CaseTag {
        whitespace_control: WhiteSpaceControl,
        whens: Vec<ConditionalBlock>,
        default: Option<Vec<Node>>,
    },
    CycleTag {
        whitespace_control: WhiteSpaceControl,
        name: Option<String>,
        args: Vec<Primitive>,
    },
    DecrementTag {
        whitespace_control: WhiteSpaceControl,
        name: String,
    },
    IncrementTag {
        whitespace_control: WhiteSpaceControl,
        name: String,
    },
    EchoTag {
        whitespace_control: WhiteSpaceControl,
        expression: FilteredExpression,
    },
    ForTag {
        whitespace_control: WhiteSpaceControl,
        name: String,
        iterable: Primitive,
        limit: Primitive,
        offset: Primitive,
        reversed: bool,
        block: Vec<Node>,
    },
    BreakTag {
        whitespace_control: WhiteSpaceControl,
    },
    ContinueTag {
        whitespace_control: WhiteSpaceControl,
    },
    IfTag {
        whitespace_control: WhiteSpaceControl,
        condition: Box<ConditionalBlock>,
        alternatives: Vec<ConditionalBlock>,
        default: Option<Vec<Node>>,
    },
    UnlessTag {
        whitespace_control: WhiteSpaceControl,
        condition: Box<ConditionalBlock>,
        alternatives: Vec<ConditionalBlock>,
        default: Option<Vec<Node>>,
    },
    IncludeTag {
        whitespace_control: WhiteSpaceControl,
        target: Primitive,
        repeat: bool,
        variable: Primitive,
        alias: String,
        args: Vec<CommonArgument>,
    },
    RenderTag {
        whitespace_control: WhiteSpaceControl,
        target: Primitive,
        repeat: bool,
        variable: Primitive,
        alias: String,
        args: Vec<CommonArgument>,
    },
    LiquidTag {
        whitespace_control: WhiteSpaceControl,
        block: Vec<Node>,
    },
    TagExtension {
        whitespace_control: WhiteSpaceControl,
        name: String,
        args: Vec<CommonArgument>,
        block: Option<Vec<Node>>,
    },
}

#[derive(Debug)]
pub struct FilteredExpression {
    pub left: Primitive,
    pub filters: Vec<Filter>,
    pub condition: BooleanExpression,
    pub alternative: Option<Primitive>,
    pub alternative_filters: Vec<Filter>,
    pub tail_filters: Vec<Filter>,
}

#[derive(Debug)]
pub struct InfixExpression {
    pub left: Box<BooleanExpression>,
    pub operator: String, // TODO: or enum
    pub right: Box<BooleanExpression>,
}

#[derive(Debug)]
pub struct PrefixExpression {
    pub operator: String, // TODO: or enum
    pub right: Box<BooleanExpression>,
}

#[derive(Debug)]
pub enum BooleanExpression {
    Primitive { expr: Primitive },
    Prefix { expr: PrefixExpression },
    Infix { expr: InfixExpression },
}

#[derive(Debug)]
pub struct Filter {
    pub name: String,
    pub args: Vec<CommonArgument>,
}

#[derive(Debug)]
pub enum Primitive {
    True_ {},
    False_ {},
    Null_ {},
    Int { value: i64 },
    Float { value: f64 },
    StringLiteral { value: String },
    Range { start: i64, stop: i64 },
    Query { path: Query },
}

#[derive(Debug)]
pub struct ConditionalBlock {
    pub condition: BooleanExpression,
    pub block: Vec<Node>,
}

#[derive(Debug)]
pub struct CommonArgument {
    pub value: Option<Primitive>,
    pub name: Option<String>,
}

#[derive(Debug)]
pub struct WhiteSpaceControl {
    pub left: WhiteSpace,
    pub right: WhiteSpace,
}

#[derive(Debug)]
pub enum WhiteSpace {
    Plus,
    Minus,
    Smart,
    Default,
}
