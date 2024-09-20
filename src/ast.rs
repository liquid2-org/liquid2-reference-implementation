//! Liquid template syntax tree
//!
use pyo3::prelude::*;
use std::fmt::{self};

use crate::query::Query;

#[pyclass]
#[derive(Debug, Clone)]
pub struct Template {
    #[pyo3(get)]
    pub liquid: Vec<Node>,
}

impl fmt::Display for Template {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", display_block(&self.liquid))
    }
}

#[pymethods]
impl Template {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[allow(non_upper_case_globals)]
#[pyclass]
#[derive(Debug, Clone)]
pub enum Node {
    EOI {},
    Content {
        text: String,
    },
    Output {
        wc: WhitespaceControl,
        expression: FilteredExpression,
    },
    Raw {
        wc: (WhitespaceControl, WhitespaceControl),
        text: String,
    },
    Comment {
        wc: WhitespaceControl,
        text: String,
        hashes: String,
    },
    AssignTag {
        wc: WhitespaceControl,
        identifier: String,
        expression: FilteredExpression,
    },
    CaptureTag {
        wc: (WhitespaceControl, WhitespaceControl),
        identifier: String,
        block: Vec<Node>,
    },
    CaseTag {
        wc: (WhitespaceControl, WhitespaceControl),
        arg: Primitive,
        whens: Vec<WhenTag>,
        default: Option<ElseTag>,
    },
    CycleTag {
        wc: WhitespaceControl,
        name: Option<String>,
        args: Vec<Primitive>,
    },
    DecrementTag {
        wc: WhitespaceControl,
        name: String,
    },
    IncrementTag {
        wc: WhitespaceControl,
        name: String,
    },
    EchoTag {
        wc: WhitespaceControl,
        expression: FilteredExpression,
    },
    ForTag {
        wc: (WhitespaceControl, WhitespaceControl),
        name: String,
        iterable: Primitive,
        limit: Option<Primitive>,
        offset: Option<Primitive>,
        reversed: bool,
        block: Vec<Node>,
        default: Option<ElseTag>,
    },
    BreakTag {
        wc: WhitespaceControl,
    },
    ContinueTag {
        wc: WhitespaceControl,
    },
    IfTag {
        wc: (WhitespaceControl, WhitespaceControl),
        condition: BooleanExpression,
        block: Vec<Node>,
        alternatives: Vec<ElsifTag>,
        default: Option<ElseTag>,
    },
    UnlessTag {
        wc: (WhitespaceControl, WhitespaceControl),
        condition: BooleanExpression,
        block: Vec<Node>,
        alternatives: Vec<ElsifTag>,
        default: Option<ElseTag>,
    },
    IncludeTag {
        wc: WhitespaceControl,
        target: Primitive,
        repeat: bool,
        variable: Option<Primitive>,
        alias: Option<String>,
        args: Option<Vec<CommonArgument>>,
    },
    RenderTag {
        wc: WhitespaceControl,
        target: Primitive,
        repeat: bool,
        variable: Option<Primitive>,
        alias: Option<String>,
        args: Option<Vec<CommonArgument>>,
    },
    LiquidTag {
        wc: WhitespaceControl,
        block: Vec<Node>,
    },
    TagExtension {
        wc: (WhitespaceControl, Option<WhitespaceControl>),
        name: String,
        args: Vec<CommonArgument>,
        block: Option<Vec<Node>>,
        tags: Option<Vec<Node>>, // XXX: Nested tags, like `else` in a `for` loop, or `when` in a `case` block
    },
}

impl fmt::Display for Node {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Node::EOI {} => Ok(()),
            Node::Content { text } => f.write_str(text),
            Node::Output { wc, expression } => {
                write!(f, "{{{{{} {} {}}}}}", wc.left, expression, wc.right)
            }
            Node::Raw { wc, text } => {
                write!(
                    f,
                    "{{%{} raw {}%}}{}{{%{} endraw {}%}}",
                    wc.0.left, wc.0.right, text, wc.1.left, wc.1.right
                )
            }
            Node::Comment { wc, text, hashes } => {
                write!(f, "{{{}{}{}{}{}}}", hashes, wc.left, text, wc.right, hashes)
            }
            Node::AssignTag {
                wc,
                identifier,
                expression,
            } => {
                write!(
                    f,
                    "{{%{} assign {} = {} {}%}}",
                    wc.left, identifier, expression, wc.right
                )
            }
            Node::CaptureTag {
                wc,
                identifier,
                block,
            } => {
                write!(
                    f,
                    "{{%{} capture {} {}%}}{}{{%{} endcapture {}%}}",
                    wc.0.left,
                    identifier,
                    wc.0.right,
                    display_block(block),
                    wc.1.left,
                    wc.1.right
                )
            }
            Node::CaseTag {
                wc,
                arg,
                whens,
                default,
            } => {
                // TODO: we don't retain content between `case` and the first `when`
                write!(f, "{{%{} case {} {}%}}\n", wc.0.left, arg, wc.0.right)?;

                whens.iter().try_for_each(|when| write!(f, "{when}"))?;

                default
                    .as_ref()
                    .and_then(|t| Some(write!(f, "{t}")))
                    .transpose()?;

                write!(f, "{{%{} endcase {}%}}", wc.1.left, wc.1.right)
            }
            Node::CycleTag { wc, name, args } => {
                write!(f, "{{%{} cycle ", wc.left)?;

                name.as_ref()
                    .and_then(|s| Some(write!(f, "{s}: ")))
                    .transpose()?;

                write!(
                    f,
                    "{}",
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<String>>()
                        .join(", ")
                )?;

                write!(f, " {}%}}", wc.right)
            }
            Node::DecrementTag { wc, name } => {
                write!(f, "{{%{} decrement {} {}%}}", wc.left, name, wc.right)
            }
            Node::IncrementTag { wc, name } => {
                write!(f, "{{%{} increment {} {}%}}", wc.left, name, wc.right)
            }
            Node::EchoTag { wc, expression } => {
                write!(f, "{{%{} echo {} {}%}}", wc.left, expression, wc.right)
            }
            Node::ForTag {
                wc,
                name,
                iterable,
                limit,
                offset,
                reversed,
                block,
                default,
            } => {
                write!(f, "{{%{} for {} in {} ", wc.0.left, name, iterable)?;

                limit
                    .as_ref()
                    .and_then(|p| Some(write!(f, "limit: {p}, ")))
                    .transpose()?;

                offset
                    .as_ref()
                    .and_then(|p| Some(write!(f, "offset: {p}, ")))
                    .transpose()?;

                if *reversed == true {
                    write!(f, "reversed ")?;
                }

                write!(f, "{}%}}{}", wc.0.right, display_block(block))?;

                default
                    .as_ref()
                    .and_then(|t| Some(write!(f, "{t}")))
                    .transpose()?;

                write!(f, "{{%{} endfor {}%}}", wc.1.left, wc.1.right)
            }
            Node::BreakTag { wc } => {
                write!(f, "{{%{} break {}%}}", wc.left, wc.right)
            }
            Node::ContinueTag { wc } => {
                write!(f, "{{%{} continue {}%}}", wc.left, wc.right)
            }
            Node::IfTag {
                wc,
                condition,
                block,
                alternatives,
                default,
            } => {
                write!(
                    f,
                    "{{%{} if {} {}%}}{}",
                    wc.0.left,
                    condition,
                    wc.0.right,
                    display_block(block)
                )?;

                alternatives.iter().try_for_each(|t| write!(f, "{t}"))?;

                default
                    .as_ref()
                    .and_then(|t| Some(write!(f, "{t}")))
                    .transpose()?;

                write!(f, "{{%{} endif {}%}}", wc.1.left, wc.1.right)
            }
            Node::UnlessTag {
                wc,
                condition,
                block,
                alternatives,
                default,
            } => {
                write!(
                    f,
                    "{{%{} unless {} {}%}}{}",
                    wc.0.left,
                    condition,
                    wc.0.right,
                    display_block(block)
                )?;

                alternatives.iter().try_for_each(|t| write!(f, "{t}"))?;

                default
                    .as_ref()
                    .and_then(|t| Some(write!(f, "{t}")))
                    .transpose()?;

                write!(f, "{{%{} unless {}%}}", wc.1.left, wc.1.right)
            }
            Node::IncludeTag {
                wc,
                target,
                repeat,
                variable,
                alias,
                args,
            } => {
                write!(f, "{{%{} include {} ", wc.left, target)?;

                if variable.is_some() {
                    if *repeat == true {
                        write!(f, "for {} ", variable.as_ref().unwrap())?;
                    } else {
                        write!(f, "with {} ", variable.as_ref().unwrap())?;
                    }
                };

                alias
                    .as_ref()
                    .and_then(|s| Some(write!(f, "as {s} ")))
                    .transpose()?;

                args.as_ref().and_then(|a| {
                    Some(write!(
                        f,
                        "{} ",
                        a.iter()
                            .map(|b| b.to_string())
                            .collect::<Vec<String>>()
                            .join(", ")
                    ))
                });

                write!(f, "{}%}}", wc.right)
            }
            Node::RenderTag {
                wc,
                target,
                repeat,
                variable,
                alias,
                args,
            } => {
                write!(f, "{{%{} render {} ", wc.left, target)?;

                if variable.is_some() {
                    if *repeat == true {
                        write!(f, "for {} ", variable.as_ref().unwrap())?;
                    } else {
                        write!(f, "with {} ", variable.as_ref().unwrap())?;
                    }
                };

                alias
                    .as_ref()
                    .and_then(|s| Some(write!(f, "as {s} ")))
                    .transpose()?;

                args.as_ref().and_then(|a| {
                    Some(write!(
                        f,
                        "{} ",
                        a.iter()
                            .map(|b| b.to_string())
                            .collect::<Vec<String>>()
                            .join(", ")
                    ))
                });

                write!(f, "{}%}}", wc.right)
            }
            Node::LiquidTag { wc, block } => {
                // TODO: indent line statements
                write!(
                    f,
                    "{{%{} liquid\n{}\n{}%}}",
                    wc.left,
                    display_line_block(block),
                    wc.right
                )
            }
            Node::TagExtension {
                wc,
                name,
                args,
                block,
                tags,
            } => todo!(),
        }
    }
}

#[pymethods]
impl Node {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct FilteredExpression {
    #[pyo3(get)]
    pub left: Primitive,
    #[pyo3(get)]
    pub filters: Option<Vec<Filter>>,
    #[pyo3(get)]
    pub condition: Option<InlineCondition>,
}

impl fmt::Display for FilteredExpression {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.left)?;

        self.filters.as_ref().and_then(|filters| {
            // XXX: bit of a hack, because filters can be an empty vec
            if filters.len() > 0 {
                Some(write!(
                    f,
                    " | {}",
                    filters
                        .iter()
                        .map(|f| f.to_string())
                        .collect::<Vec<String>>()
                        .join(" | ")
                ))
            } else {
                None
            }
        });

        self.condition
            .as_ref()
            .and_then(|condition| Some(write!(f, " {}", condition)));

        Ok(())
    }
}

#[pymethods]
impl FilteredExpression {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct InlineCondition {
    #[pyo3(get)]
    pub expr: BooleanExpression,
    #[pyo3(get)]
    pub alternative: Option<Primitive>,
    #[pyo3(get)]
    pub alternative_filters: Option<Vec<Filter>>,
    #[pyo3(get)]
    pub tail_filters: Option<Vec<Filter>>,
}

impl fmt::Display for InlineCondition {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "if {}", self.expr)?;

        self.alternative
            .as_ref()
            .and_then(|alt| Some(write!(f, " else {alt}")));

        self.alternative_filters.as_ref().and_then(|filters| {
            // XXX: bit of a hack, because filters can be an empty vec
            if filters.len() > 0 {
                Some(write!(
                    f,
                    " | {}",
                    filters
                        .iter()
                        .map(|f| f.to_string())
                        .collect::<Vec<String>>()
                        .join(" | ")
                ))
            } else {
                None
            }
        });

        self.tail_filters.as_ref().and_then(|filters| {
            Some(write!(
                f,
                " || {}",
                filters
                    .iter()
                    .map(|f| f.to_string())
                    .collect::<Vec<String>>()
                    .join(" | ")
            ))
        });

        Ok(())
    }
}

#[pymethods]
impl InlineCondition {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum BooleanExpression {
    Primitive {
        expr: Primitive,
    },
    LogicalNot {
        expr: Box<BooleanExpression>,
    },
    Logical {
        left: Box<BooleanExpression>,
        operator: BooleanOperator,
        right: Box<BooleanExpression>,
    },
    Comparison {
        left: Primitive,
        operator: CompareOperator,
        right: Primitive,
    },
    Membership {
        left: Primitive,
        operator: MembershipOperator,
        right: Primitive,
    },
}

impl fmt::Display for BooleanExpression {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BooleanExpression::Primitive { expr } => write!(f, "{expr}"),
            BooleanExpression::LogicalNot { expr } => write!(f, "not ({expr})"),
            BooleanExpression::Logical {
                left,
                operator,
                right,
            } => write!(f, "{left} {operator}, {right}"),
            BooleanExpression::Comparison {
                left,
                operator,
                right,
            } => write!(f, "{left} {operator}, {right}"),
            BooleanExpression::Membership {
                left,
                operator,
                right,
            } => write!(f, "{left} {operator}, {right}"),
        }
    }
}

#[pymethods]
impl BooleanExpression {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum BooleanOperator {
    And {},
    Or {},
}

impl fmt::Display for BooleanOperator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BooleanOperator::And {} => f.write_str("and"),
            BooleanOperator::Or {} => f.write_str("or"),
        }
    }
}

#[pymethods]
impl BooleanOperator {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum CompareOperator {
    Eq {},
    Ne {},
    Ge {},
    Gt {},
    Le {},
    Lt {},
}

impl fmt::Display for CompareOperator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CompareOperator::Eq {} => f.write_str("=="),
            CompareOperator::Ne {} => f.write_str("!="),
            CompareOperator::Ge {} => f.write_str(">="),
            CompareOperator::Gt {} => f.write_str(">"),
            CompareOperator::Le {} => f.write_str("<="),
            &CompareOperator::Lt {} => f.write_str("<"),
        }
    }
}

#[pymethods]
impl CompareOperator {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum MembershipOperator {
    In {},
    NotIn {},
    Contains {},
    NotContains {},
}

impl fmt::Display for MembershipOperator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MembershipOperator::In {} => f.write_str("in"),
            MembershipOperator::NotIn {} => f.write_str("not in"),
            MembershipOperator::Contains {} => f.write_str("contains"),
            &MembershipOperator::NotContains {} => f.write_str("not contains"),
        }
    }
}

#[pymethods]
impl MembershipOperator {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Filter {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub args: Option<Vec<CommonArgument>>,
}

impl fmt::Display for Filter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Filter {
                name,
                args: Some(arguments),
            } => {
                write!(
                    f,
                    "{}: {}",
                    name,
                    arguments
                        .iter()
                        .map(|s| s.to_string())
                        .collect::<Vec<String>>()
                        .join(", "),
                )
            }
            Filter { name, args: None } => write!(f, "{name}"),
        }
    }
}

#[pymethods]
impl Filter {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub enum Primitive {
    TrueLiteral {},
    FalseLiteral {},
    NullLiteral {},
    Integer { value: i64 },
    Float { value: f64 },
    StringLiteral { value: String },
    Range { start: i64, stop: i64 },
    Query { path: Query },
}

impl fmt::Display for Primitive {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Primitive::TrueLiteral {} => f.write_str("true"),
            Primitive::FalseLiteral {} => f.write_str("false"),
            Primitive::NullLiteral {} => f.write_str("null"),
            Primitive::Integer { value } => write!(f, "{value}"),
            Primitive::Float { value } => write!(f, "{value}"),
            Primitive::StringLiteral { value } => write!(f, "'{value}'"),
            Primitive::Range { start, stop } => write!(f, "({start}..{stop})"),
            // XXX: JSONPath queries are displayed in their canonical format
            Primitive::Query { path } => write!(f, "{path}"),
        }
    }
}

#[pymethods]
impl Primitive {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct WhenTag {
    #[pyo3(get)]
    pub wc: WhitespaceControl,
    #[pyo3(get)]
    pub args: Vec<Primitive>,
    #[pyo3(get)]
    pub block: Vec<Node>,
}

impl fmt::Display for WhenTag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{{%{} when {} {}%}}{}",
            self.wc.left,
            self.args
                .iter()
                .map(|s| s.to_string())
                .collect::<Vec<String>>()
                .join(", "),
            self.wc.right,
            display_block(&self.block)
        )
    }
}

#[pymethods]
impl WhenTag {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ElseTag {
    #[pyo3(get)]
    pub wc: WhitespaceControl,
    #[pyo3(get)]
    pub block: Vec<Node>,
}

impl fmt::Display for ElseTag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{{%{} else {}%}}{}",
            self.wc.left,
            self.wc.right,
            display_block(&self.block)
        )
    }
}

#[pymethods]
impl ElseTag {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ElsifTag {
    #[pyo3(get)]
    pub wc: WhitespaceControl,
    #[pyo3(get)]
    pub condition: BooleanExpression,
    #[pyo3(get)]
    pub block: Vec<Node>,
}

impl fmt::Display for ElsifTag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{{%{} elsif {} {}%}}{}",
            self.wc.left,
            self.condition,
            self.wc.right,
            display_block(&self.block)
        )
    }
}

#[pymethods]
impl ElsifTag {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct CommonArgument {
    #[pyo3(get)]
    pub value: Option<Primitive>,
    #[pyo3(get)]
    pub name: Option<String>,
}

impl fmt::Display for CommonArgument {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CommonArgument {
                value: Some(v),
                name: Some(k),
            } => write!(f, "{}:{}", k, v),
            CommonArgument {
                value: Some(v),
                name: None,
            } => write!(f, "{}", v),
            CommonArgument {
                value: None,
                name: Some(k),
            } => write!(f, "{}", k),
            _ => Ok(()),
        }
    }
}

#[pymethods]
impl CommonArgument {
    fn __str__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct WhitespaceControl {
    #[pyo3(get)]
    pub left: Whitespace,
    #[pyo3(get)]
    pub right: Whitespace,
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

fn display_block(block: &[Node]) -> String {
    block
        .iter()
        .map(|n| n.to_string())
        .collect::<Vec<String>>()
        .join("")
}

fn display_line_block(block: &[Node]) -> String {
    block
        .iter()
        .map(|n| n.to_string())
        .collect::<Vec<String>>()
        .join("\n")
}

impl<'py> pyo3::FromPyObject<'py> for Box<BooleanExpression> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        ob.extract::<BooleanExpression>().map(Box::new)
    }
}

impl pyo3::IntoPy<pyo3::PyObject> for Box<BooleanExpression> {
    fn into_py(self, py: pyo3::Python<'_>) -> pyo3::PyObject {
        (*self).into_py(py)
    }
}
