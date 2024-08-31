//! Liquid template syntax tree
//!

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
}

#[derive(Debug)]
pub struct FilteredExpression {
    left: Primitive,
    filters: Vec<Filter>,
    condition: BooleanExpression,
    alternative: Option<Primitive>,
    alternative_filters: Vec<Filter>,
    tail_filters: Vec<Filter>,
}

#[derive(Debug)]
pub struct InfixExpression {
    left: Box<BooleanExpression>,
    operator: String, // TODO: or enum
    right: Box<BooleanExpression>,
}

#[derive(Debug)]
pub struct PrefixExpression {
    operator: String, // TODO: or enum
    right: Box<BooleanExpression>,
}

#[derive(Debug)]
pub enum BooleanExpression {
    Primitive { expr: Primitive },
    Prefix { expr: PrefixExpression },
    Infix { expr: InfixExpression },
}

#[derive(Debug)]
pub struct Filter {
    name: String,
    args: Vec<CommonArgument>,
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
    Query { path: JSONPathQuery },
}

#[derive(Debug)]
pub struct ConditionalBlock {
    condition: BooleanExpression,
    block: Vec<Node>,
}

#[derive(Debug)]
pub struct CommonArgument {
    value: Primitive,
    name: Option<String>,
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
