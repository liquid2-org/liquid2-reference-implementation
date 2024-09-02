use std::{collections::HashMap, ops::RangeInclusive};

use pest::{iterators::Pair, iterators::Pairs, Parser};
use pest_derive::Parser;

use crate::{
    ast::{Node, Template, WhiteSpace, WhiteSpaceControl},
    errors::LiquidError,
    query::{ComparisonOperator, FilterExpression, LogicalOperator, Query, Segment, Selector},
};

#[derive(Parser)]
#[grammar = "liquid2.pest"]
struct Liquid;

pub struct LiquidParser {
    pub tags: HashMap<String, bool>,
    pub query_parser: QueryParser,
}

impl LiquidParser {
    pub fn new() -> Self {
        LiquidParser {
            tags: standard_tags(),
            query_parser: QueryParser::new(),
        }
    }

    pub fn parse_dump(&self, template: &str) {
        let elements = Liquid::parse(Rule::liquid, template);
        println!("{:#?}", elements);
    }

    pub fn parse(&self, template: &str) -> Result<Template, LiquidError> {
        let liquid: Result<Vec<_>, _> = Liquid::parse(Rule::liquid, template)
            .map_err(|err| LiquidError::syntax(err.to_string()))?
            .map(|markup| self.parse_markup(markup))
            .collect();

        Ok(Template { liquid: liquid? })
    }

    fn parse_markup(&self, markup: Pair<Rule>) -> Result<Node, LiquidError> {
        Ok(match markup.as_rule() {
            Rule::content => Node::Content {
                text: markup.as_str().to_owned(),
            },
            Rule::raw_tag => self.parse_raw(markup),
            Rule::EOI => Node::EOI {},
            _ => todo!("Rule: {:#?}", markup),
        })
    }

    fn parse_raw(&self, tag: Pair<Rule>) -> Node {
        let mut it = tag.into_inner();
        let start_wc_left = WhiteSpace::from_str(it.next().unwrap().as_str());
        let start_wc_right = WhiteSpace::from_str(it.next().unwrap().as_str());
        let raw_content = it.next().unwrap().as_str().to_owned();
        let end_wc_left = WhiteSpace::from_str(it.next().unwrap().as_str());
        let end_wc_right = WhiteSpace::from_str(it.next().unwrap().as_str());

        Node::Raw {
            whitespace_control: (
                WhiteSpaceControl {
                    left: start_wc_left,
                    right: start_wc_right,
                },
                WhiteSpaceControl {
                    left: end_wc_left,
                    right: end_wc_right,
                },
            ),
            text: raw_content,
        }
    }
}

pub struct QueryParser {
    pub index_range: RangeInclusive<i64>,
    pub functions: HashMap<String, FunctionSignature>,
}

impl QueryParser {
    pub fn new() -> Self {
        QueryParser {
            index_range: ((-2_i64).pow(53) + 1..=2_i64.pow(53) - 1),
            functions: standard_functions(),
        }
    }

    pub fn parse(&self, segments: Pairs<Rule>) -> Result<Query, LiquidError> {
        let segments: Result<Vec<_>, _> = segments
            .map(|segment| self.parse_segment(segment))
            .collect();

        Ok(Query {
            segments: segments?,
        })
    }

    fn parse_segment(&self, segment: Pair<Rule>) -> Result<Segment, LiquidError> {
        Ok(match segment.as_rule() {
            Rule::child_segment => Segment::Child {
                selectors: self.parse_segment_inner(segment.into_inner().next().unwrap())?,
            },
            Rule::descendant_segment => Segment::Recursive {
                selectors: self.parse_segment_inner(segment.into_inner().next().unwrap())?,
            },
            Rule::name_segment | Rule::index_segment => Segment::Child {
                selectors: vec![self.parse_selector(segment.into_inner().next().unwrap())?],
            },
            Rule::EOI => Segment::Eoi {},
            _ => unreachable!(),
        })
    }

    fn parse_segment_inner(&self, segment: Pair<Rule>) -> Result<Vec<Selector>, LiquidError> {
        Ok(match segment.as_rule() {
            Rule::bracketed_selection => {
                let seg: Result<Vec<_>, _> = segment
                    .into_inner()
                    .map(|selector| self.parse_selector(selector))
                    .collect();
                seg?
            }
            Rule::wildcard_selector => vec![Selector::Wild {}],
            Rule::member_name_shorthand => vec![Selector::Name {
                // for child_segment
                name: segment.as_str().to_owned(),
            }],
            _ => unreachable!(),
        })
    }

    fn parse_selector(&self, selector: Pair<Rule>) -> Result<Selector, LiquidError> {
        Ok(match selector.as_rule() {
            Rule::double_quoted => Selector::Name {
                name: unescape_string(selector.as_str()),
            },
            Rule::single_quoted => Selector::Name {
                name: unescape_string(&selector.as_str().replace("\\'", "'")),
            },
            Rule::wildcard_selector => Selector::Wild {},
            Rule::slice_selector => self.parse_slice_selector(selector)?,
            Rule::index_selector => Selector::Index {
                index: self.parse_i_json_int(selector.as_str())?,
            },
            Rule::filter_selector => self.parse_filter_selector(selector)?,
            Rule::member_name_shorthand => Selector::Name {
                // for name_segment
                name: selector.as_str().to_owned(),
            },
            Rule::singular_query_selector => self.parse_singular_query_selector(selector)?,
            _ => unreachable!(),
        })
    }

    fn parse_slice_selector(&self, selector: Pair<Rule>) -> Result<Selector, LiquidError> {
        let mut start: Option<i64> = None;
        let mut stop: Option<i64> = None;
        let mut step: Option<i64> = None;

        for i in selector.into_inner() {
            match i.as_rule() {
                Rule::start => start = Some(self.parse_i_json_int(i.as_str())?),
                Rule::stop => stop = Some(self.parse_i_json_int(i.as_str())?),
                Rule::step => step = Some(self.parse_i_json_int(i.as_str())?),
                _ => unreachable!(),
            }
        }

        Ok(Selector::Slice { start, stop, step })
    }

    fn parse_filter_selector(&self, selector: Pair<Rule>) -> Result<Selector, LiquidError> {
        Ok(Selector::Filter {
            expression: Box::new(
                self.parse_logical_or_expression(selector.into_inner().next().unwrap(), true)?,
            ),
        })
    }

    fn parse_singular_query_selector(&self, selector: Pair<Rule>) -> Result<Selector, LiquidError> {
        let segments: Result<Vec<_>, _> = selector
            .into_inner()
            .map(|segment| self.parse_segment(segment))
            .collect();

        Ok(Selector::SingularQuery {
            query: Box::new(Query {
                segments: segments?,
            }),
        })
    }

    fn parse_logical_or_expression(
        &self,
        expr: Pair<Rule>,
        assert_compared: bool,
    ) -> Result<FilterExpression, LiquidError> {
        let mut it = expr.into_inner();
        let mut or_expr = self.parse_logical_and_expression(it.next().unwrap(), assert_compared)?;

        if assert_compared {
            self.assert_compared(&or_expr)?;
        }

        for and_expr in it {
            let right = self.parse_logical_and_expression(and_expr, assert_compared)?;
            if assert_compared {
                self.assert_compared(&right)?;
            }
            or_expr = FilterExpression::Logical {
                left: Box::new(or_expr),
                operator: LogicalOperator::Or,
                right: Box::new(right),
            };
        }

        Ok(or_expr)
    }

    fn parse_logical_and_expression(
        &self,
        expr: Pair<Rule>,
        assert_compared: bool,
    ) -> Result<FilterExpression, LiquidError> {
        let mut it = expr.into_inner();
        let mut and_expr = self.parse_basic_expression(it.next().unwrap())?;

        if assert_compared {
            self.assert_compared(&and_expr)?;
        }

        for basic_expr in it {
            let right = self.parse_basic_expression(basic_expr)?;

            if assert_compared {
                self.assert_compared(&right)?;
            }

            and_expr = FilterExpression::Logical {
                left: Box::new(and_expr),
                operator: LogicalOperator::And,
                right: Box::new(right),
            };
        }

        Ok(and_expr)
    }

    fn parse_basic_expression(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        match expr.as_rule() {
            Rule::paren_expr => self.parse_paren_expression(expr),
            Rule::comparison_expr => self.parse_comparison_expression(expr),
            Rule::test_expr => self.parse_test_expression(expr),
            _ => unreachable!(),
        }
    }

    fn parse_paren_expression(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        let mut it = expr.into_inner();
        let p = it.next().unwrap();
        match p.as_rule() {
            Rule::logical_not_op => Ok(FilterExpression::Not {
                expression: Box::new(self.parse_logical_or_expression(it.next().unwrap(), true)?),
            }),
            Rule::logical_or_expr => self.parse_logical_or_expression(p, true),
            _ => unreachable!(),
        }
    }

    fn parse_comparison_expression(
        &self,
        expr: Pair<Rule>,
    ) -> Result<FilterExpression, LiquidError> {
        let mut it = expr.into_inner();
        let left = self.parse_comparable(it.next().unwrap())?;

        let operator = match it.next().unwrap().as_str() {
            "==" => ComparisonOperator::Eq,
            "!=" => ComparisonOperator::Ne,
            "<=" => ComparisonOperator::Le,
            ">=" => ComparisonOperator::Ge,
            "<" => ComparisonOperator::Lt,
            ">" => ComparisonOperator::Gt,
            _ => unreachable!(),
        };

        let right = self.parse_comparable(it.next().unwrap())?;
        self.assert_comparable(&left)?;
        self.assert_comparable(&right)?;

        Ok(FilterExpression::Comparison {
            left: Box::new(left),
            operator,
            right: Box::new(right),
        })
    }

    fn parse_comparable(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        Ok(match expr.as_rule() {
            Rule::number => self.parse_number(expr)?,
            Rule::double_quoted => FilterExpression::StringLiteral {
                value: unescape_string(expr.as_str()),
            },
            Rule::single_quoted => FilterExpression::StringLiteral {
                value: unescape_string(&expr.as_str().replace("\\'", "'")),
            },
            Rule::true_literal => FilterExpression::True_ {},
            Rule::false_literal => FilterExpression::False_ {},
            Rule::null => FilterExpression::Null {},
            Rule::rel_singular_query => {
                let segments: Result<Vec<_>, _> = expr
                    .into_inner()
                    .map(|segment| self.parse_segment(segment))
                    .collect();

                FilterExpression::RelativeQuery {
                    query: Box::new(Query {
                        segments: segments?,
                    }),
                }
            }
            Rule::abs_singular_query => {
                let segments: Result<Vec<_>, _> = expr
                    .into_inner()
                    .map(|segment| self.parse_segment(segment))
                    .collect();

                FilterExpression::RootQuery {
                    query: Box::new(Query {
                        segments: segments?,
                    }),
                }
            }
            Rule::function_expr => self.parse_function_expression(expr)?,
            _ => unreachable!(),
        })
    }

    fn parse_number(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        if expr.as_str() == "-0" {
            return Ok(FilterExpression::Int { value: 0 });
        }

        // TODO: change pest grammar to indicate positive or negative exponent?
        let mut it = expr.into_inner();
        let mut is_float = false;
        let mut n = it.next().unwrap().as_str().to_string(); // int

        if let Some(pair) = it.next() {
            match pair.as_rule() {
                Rule::frac => {
                    is_float = true;
                    n.push_str(pair.as_str());
                }
                Rule::exp => {
                    let exp_str = pair.as_str();
                    if exp_str.contains('-') {
                        is_float = true;
                    }
                    n.push_str(exp_str);
                }
                _ => unreachable!(),
            }
        }

        if let Some(pair) = it.next() {
            let exp_str = pair.as_str();
            if exp_str.contains('-') {
                is_float = true;
            }
            n.push_str(exp_str);
        }

        if is_float {
            Ok(FilterExpression::Float {
                value: n
                    .parse::<f64>()
                    .map_err(|_| LiquidError::syntax(String::from("invalid float literal")))?,
            })
        } else {
            Ok(FilterExpression::Int {
                value: n
                    .parse::<f64>()
                    .map_err(|_| LiquidError::syntax(String::from("invalid integer literal")))?
                    as i64,
            })
        }
    }

    fn parse_test_expression(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        let mut it = expr.into_inner();
        let pair = it.next().unwrap();
        Ok(match pair.as_rule() {
            Rule::logical_not_op => FilterExpression::Not {
                expression: Box::new(self.parse_test_expression_inner(it.next().unwrap())?),
            },
            _ => self.parse_test_expression_inner(pair)?,
        })
    }

    fn parse_test_expression_inner(
        &self,
        expr: Pair<Rule>,
    ) -> Result<FilterExpression, LiquidError> {
        Ok(match expr.as_rule() {
            Rule::rel_query => {
                let segments: Result<Vec<_>, _> = expr
                    .into_inner()
                    .map(|segment| self.parse_segment(segment))
                    .collect();

                FilterExpression::RelativeQuery {
                    query: Box::new(Query {
                        segments: segments?,
                    }),
                }
            }
            Rule::root_query => {
                let segments: Result<Vec<_>, _> = expr
                    .into_inner()
                    .map(|segment| self.parse_segment(segment))
                    .collect();

                FilterExpression::RootQuery {
                    query: Box::new(Query {
                        segments: segments?,
                    }),
                }
            }
            Rule::function_expr => self.parse_function_expression(expr)?,
            _ => unreachable!(),
        })
    }

    fn parse_function_expression(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        let mut it = expr.into_inner();
        let name = it.next().unwrap().as_str();
        let args: Result<Vec<_>, _> = it.map(|ex| self.parse_function_argument(ex)).collect();

        Ok(FilterExpression::Function {
            name: name.to_string(),
            args: self.assert_well_typed(name, args?)?,
        })
    }

    fn parse_function_argument(&self, expr: Pair<Rule>) -> Result<FilterExpression, LiquidError> {
        Ok(match expr.as_rule() {
            Rule::number => self.parse_number(expr)?,
            Rule::double_quoted => FilterExpression::StringLiteral {
                value: unescape_string(expr.as_str()),
            },
            Rule::single_quoted => FilterExpression::StringLiteral {
                value: unescape_string(&expr.as_str().replace("\\'", "'")),
            },
            Rule::true_literal => FilterExpression::True_ {},
            Rule::false_literal => FilterExpression::False_ {},
            Rule::null => FilterExpression::Null {},
            Rule::rel_query => {
                let segments: Result<Vec<_>, _> = expr
                    .into_inner()
                    .map(|segment| self.parse_segment(segment))
                    .collect();

                FilterExpression::RelativeQuery {
                    query: Box::new(Query {
                        segments: segments?,
                    }),
                }
            }
            Rule::root_query => {
                let segments: Result<Vec<_>, _> = expr
                    .into_inner()
                    .map(|segment| self.parse_segment(segment))
                    .collect();

                FilterExpression::RootQuery {
                    query: Box::new(Query {
                        segments: segments?,
                    }),
                }
            }
            Rule::logical_or_expr => self.parse_logical_or_expression(expr, false)?,
            Rule::function_expr => self.parse_function_expression(expr)?,
            _ => unreachable!(),
        })
    }

    fn parse_i_json_int(&self, value: &str) -> Result<i64, LiquidError> {
        let i = value
            .parse::<i64>()
            .map_err(|_| LiquidError::syntax(format!("index out of range `{}`", value)))?;

        if !self.index_range.contains(&i) {
            return Err(LiquidError::syntax(format!(
                "index out of range `{}`",
                value
            )));
        }

        Ok(i)
    }
    fn assert_comparable(&self, expr: &FilterExpression) -> Result<(), LiquidError> {
        // TODO: accept span/position for better errors
        match expr {
            FilterExpression::RelativeQuery { query, .. }
            | FilterExpression::RootQuery { query, .. } => {
                if !query.is_singular() {
                    Err(LiquidError::typ(String::from(
                        "non-singular query is not comparable",
                    )))
                } else {
                    Ok(())
                }
            }
            FilterExpression::Function { name, .. } => {
                if let Some(FunctionSignature {
                    return_type: ExpressionType::Value,
                    ..
                }) = self.functions.get(name)
                {
                    Ok(())
                } else {
                    Err(LiquidError::typ(format!(
                        "result of {}() is not comparable",
                        name
                    )))
                }
            }
            _ => Ok(()),
        }
    }

    fn assert_compared(&self, expr: &FilterExpression) -> Result<(), LiquidError> {
        match expr {
            FilterExpression::Function { name, .. } => {
                if let Some(FunctionSignature {
                    return_type: ExpressionType::Value,
                    ..
                }) = self.functions.get(name)
                {
                    Err(LiquidError::typ(format!(
                        "result of {}() must be compared",
                        name
                    )))
                } else {
                    Ok(())
                }
            }
            _ => Ok(()),
        }
    }

    fn assert_well_typed(
        &self,
        func_name: &str,
        args: Vec<FilterExpression>,
    ) -> Result<Vec<FilterExpression>, LiquidError> {
        // TODO: accept span/position for better errors
        let signature = self
            .functions
            .get(func_name)
            .ok_or_else(|| LiquidError::name(format!("unknown function `{}`", func_name)))?;

        // correct number of arguments?
        if args.len() != signature.param_types.len() {
            return Err(LiquidError::typ(format!(
                "{}() takes {} argument{} but {} were given",
                func_name,
                signature.param_types.len(),
                if signature.param_types.len() > 1 {
                    "s"
                } else {
                    ""
                },
                args.len()
            )));
        }

        // correct argument types?
        for (idx, typ) in signature.param_types.iter().enumerate() {
            let arg = &args[idx];
            match typ {
                ExpressionType::Value => {
                    if !self.is_value_type(arg) {
                        return Err(LiquidError::typ(format!(
                            "argument {} of {}() must be of a 'Value' type",
                            idx + 1,
                            func_name
                        )));
                    }
                }
                ExpressionType::Logical => {
                    if !matches!(
                        arg,
                        FilterExpression::RelativeQuery { .. }
                            | FilterExpression::RootQuery { .. }
                            | FilterExpression::Logical { .. }
                            | FilterExpression::Comparison { .. },
                    ) {
                        return Err(LiquidError::typ(format!(
                            "argument {} of {}() must be of a 'Logical' type",
                            idx + 1,
                            func_name
                        )));
                    }
                }
                ExpressionType::Nodes => {
                    if !self.is_nodes_type(arg) {
                        return Err(LiquidError::typ(format!(
                            "argument {} of {}() must be of a 'Nodes' type",
                            idx + 1,
                            func_name
                        )));
                    }
                }
            }
        }

        Ok(args)
    }

    fn is_value_type(&self, expr: &FilterExpression) -> bool {
        // literals are values
        if expr.is_literal() {
            return true;
        }

        match expr {
            FilterExpression::RelativeQuery { query, .. }
            | FilterExpression::RootQuery { query, .. } => {
                // singular queries will be coerced to a value
                query.is_singular()
            }
            FilterExpression::Function { name, .. } => {
                // some functions return a value
                matches!(
                    self.functions.get(name),
                    Some(FunctionSignature {
                        return_type: ExpressionType::Value,
                        ..
                    })
                )
            }
            _ => false,
        }
    }

    fn is_nodes_type(&self, expr: &FilterExpression) -> bool {
        match expr {
            FilterExpression::RelativeQuery { .. } | FilterExpression::RootQuery { .. } => true,
            FilterExpression::Function { name, .. } => {
                matches!(
                    self.functions.get(name),
                    Some(FunctionSignature {
                        return_type: ExpressionType::Nodes,
                        ..
                    })
                )
            }
            _ => false,
        }
    }
}

fn unescape_string(value: &str) -> String {
    let chars = value.chars().collect::<Vec<char>>();
    let length = chars.len();
    let mut rv = String::new();
    let mut index: usize = 0;

    while index < length {
        match chars[index] {
            '\\' => {
                index += 1;

                match chars[index] {
                    '"' => rv.push('"'),
                    '\\' => rv.push('\\'),
                    '/' => rv.push('/'),
                    'b' => rv.push('\x08'),
                    'f' => rv.push('\x0C'),
                    'n' => rv.push('\n'),
                    'r' => rv.push('\r'),
                    't' => rv.push('\t'),
                    'u' => {
                        index += 1;

                        let digits = chars
                            .get(index..index + 4)
                            .unwrap()
                            .iter()
                            .collect::<String>();

                        let mut codepoint = u32::from_str_radix(&digits, 16).unwrap();

                        if index + 5 < length && chars[index + 4] == '\\' && chars[index + 5] == 'u'
                        {
                            let digits = &chars
                                .get(index + 6..index + 10)
                                .unwrap()
                                .iter()
                                .collect::<String>();

                            let low_surrogate = u32::from_str_radix(digits, 16).unwrap();

                            codepoint =
                                0x10000 + (((codepoint & 0x03FF) << 10) | (low_surrogate & 0x03FF));

                            index += 6;
                        }

                        let unescaped = char::from_u32(codepoint).unwrap();
                        rv.push(unescaped);
                        index += 3;
                    }
                    _ => unreachable!(),
                }
            }
            c => {
                rv.push(c);
            }
        }

        index += 1;
    }

    rv
}

#[derive(Debug)]
pub enum ExpressionType {
    Logical,
    Nodes,
    Value,
}

pub struct FunctionSignature {
    pub param_types: Vec<ExpressionType>,
    pub return_type: ExpressionType,
}

pub fn standard_functions() -> HashMap<String, FunctionSignature> {
    let mut functions = HashMap::new();

    functions.insert(
        "count".to_owned(),
        FunctionSignature {
            param_types: vec![ExpressionType::Nodes],
            return_type: ExpressionType::Value,
        },
    );

    functions.insert(
        "length".to_owned(),
        FunctionSignature {
            param_types: vec![ExpressionType::Value],
            return_type: ExpressionType::Value,
        },
    );

    functions.insert(
        "match".to_owned(),
        FunctionSignature {
            param_types: vec![ExpressionType::Value, ExpressionType::Value],
            return_type: ExpressionType::Logical,
        },
    );

    functions.insert(
        "search".to_owned(),
        FunctionSignature {
            param_types: vec![ExpressionType::Value, ExpressionType::Value],
            return_type: ExpressionType::Logical,
        },
    );

    functions.insert(
        "value".to_owned(),
        FunctionSignature {
            param_types: vec![ExpressionType::Nodes],
            return_type: ExpressionType::Value,
        },
    );

    functions
}

pub fn standard_tags() -> HashMap<String, bool> {
    let mut tags = HashMap::new();

    tags.insert("assign".to_owned(), false);
    tags.insert("capture".to_owned(), true);
    tags.insert("case".to_owned(), true);
    tags.insert("when".to_owned(), true);
    tags.insert("else".to_owned(), true);
    tags.insert("cycle".to_owned(), false);
    tags.insert("decrement".to_owned(), false);
    tags.insert("increment".to_owned(), false);
    tags.insert("echo".to_owned(), false);
    tags.insert("for".to_owned(), true);
    tags.insert("break".to_owned(), false);
    tags.insert("continue".to_owned(), false);
    tags.insert("if".to_owned(), true);
    tags.insert("elsif".to_owned(), true);
    tags.insert("unless".to_owned(), true);
    tags.insert("include".to_owned(), false);
    tags.insert("render".to_owned(), false);
    tags.insert("liquid".to_owned(), false);

    tags
}
