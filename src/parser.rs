use std::{
    collections::{HashMap, HashSet},
    ops::RangeInclusive,
};

use pest::{iterators::Pair, iterators::Pairs, Parser};
use pest_derive::Parser;

use crate::{
    ast::{
        BooleanExpression, BooleanOperator, CommonArgument, CompareOperator, ElseTag, Filter,
        FilteredExpression, InlineCondition, MembershipOperator, Node, Primitive, Template,
        WhenTag, Whitespace, WhitespaceControl,
    },
    errors::LiquidError,
    query::{ComparisonOperator, FilterExpression, LogicalOperator, Query, Segment, Selector},
};

#[derive(Parser)]
#[grammar = "liquid2.pest"]
struct Liquid;

pub struct LiquidParser {
    pub tags: HashMap<String, TagMeta>,
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
        let mut stream = Liquid::parse(Rule::liquid, template)
            .map_err(|err| LiquidError::syntax(err.to_string()))?;

        // TODO: check for EOI
        let block = self.parse_block(&mut stream, Rule::EOI)?;
        Ok(Template { liquid: block })
    }

    fn parse_block(&self, stream: &mut Pairs<Rule>, end: Rule) -> Result<Vec<Node>, LiquidError> {
        let mut block = Vec::new();
        while stream.peek().is_some_and(|r| r.as_rule() != end) {
            let markup = stream.next().unwrap();
            block.push(self.parse_markup(markup, stream)?);
        }
        Ok(block)
    }

    fn parse_named_block(
        &self,
        stream: &mut Pairs<Rule>,
        end: &str,
    ) -> Result<Vec<Node>, LiquidError> {
        let mut block = Vec::new();
        loop {
            if stream.peek().is_some_and(|r| {
                r.as_rule() == Rule::end_tag && r.into_inner().nth(1).unwrap().as_str() == end
            }) {
                break;
            }

            // TODO: handle unclosed block tag
            let markup = stream.next().unwrap();
            block.push(self.parse_markup(markup, stream)?);
        }
        Ok(block)
    }

    fn parse_block_until(
        &self,
        stream: &mut Pairs<Rule>,
        end: &HashSet<String>,
    ) -> Result<Vec<Node>, LiquidError> {
        let mut block = Vec::new();
        loop {
            if stream.peek().is_some_and(|p| match p.as_rule() {
                Rule::end_tag => end.contains(p.into_inner().nth(1).unwrap().as_str()),
                Rule::standard_tag => end.contains(p.into_inner().nth(1).unwrap().as_str()),
                // TODO: common tag
                _ => false,
            }) {
                break;
            }

            // TODO: handle unclosed block tag
            let markup = stream.next().unwrap();
            block.push(self.parse_markup(markup, stream)?);
        }
        Ok(block)
    }

    fn is_tag(&self, pair: Pair<Rule>, name: &str) -> bool {
        match pair.as_rule() {
            Rule::standard_tag => pair.into_inner().nth(1).unwrap().as_str() == name,
            Rule::end_tag => pair.into_inner().nth(1).unwrap().as_str() == name,
            // TODO: common tag
            _ => false,
        }
    }

    fn parse_markup(
        &self,
        markup: Pair<Rule>,
        stream: &mut Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        Ok(match markup.as_rule() {
            Rule::content => Node::Content {
                text: markup.as_str().to_owned(),
            },
            Rule::raw_tag => self.parse_raw(markup),
            Rule::output_statement => self.parse_output_statement(markup)?,
            Rule::standard_tag => self.parse_standard_tag(markup, stream)?,
            _ => todo!("Rule: {:#?}", markup),
        })
    }

    fn parse_raw(&self, tag: Pair<Rule>) -> Node {
        let mut it = tag.into_inner();
        let start_wc_left = Whitespace::from_str(it.next().unwrap().as_str());
        let start_wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        let raw_content = it.next().unwrap().as_str().to_owned();
        let end_wc_left = Whitespace::from_str(it.next().unwrap().as_str());
        let end_wc_right = Whitespace::from_str(it.next().unwrap().as_str());

        Node::Raw {
            whitespace_control: (
                WhitespaceControl {
                    left: start_wc_left,
                    right: start_wc_right,
                },
                WhitespaceControl {
                    left: end_wc_left,
                    right: end_wc_right,
                },
            ),
            text: raw_content,
        }
    }

    fn parse_output_statement(&self, statement: Pair<Rule>) -> Result<Node, LiquidError> {
        let mut it = statement.into_inner();
        let wc_left = Whitespace::from_str(it.next().unwrap().as_str());
        let expression = self.parse_filtered_expression(it.next().unwrap())?;
        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());

        Ok(Node::Output {
            whitespace_control: WhitespaceControl {
                left: wc_left,
                right: wc_right,
            },
            expression,
        })
    }

    fn parse_filtered_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<FilteredExpression, LiquidError> {
        let mut it = expression.into_inner();
        let left = self.parse_primitive(it.next().unwrap())?;

        let filters = it
            .next()
            .and_then(|expr| Some(self.parse_filters(expr)))
            .transpose()?;

        let condition = it
            .next()
            .and_then(|expr| Some(self.parse_inline_condition(expr)))
            .transpose()?;

        Ok(FilteredExpression {
            left,
            filters,
            condition,
        })
    }

    fn parse_filters(&self, expression: Pair<Rule>) -> Result<Vec<Filter>, LiquidError> {
        let filters: Result<Vec<_>, _> = expression
            .into_inner()
            .map(|filter| self.parse_filter(filter))
            .collect();
        filters
    }

    fn parse_filter(&self, expression: Pair<Rule>) -> Result<Filter, LiquidError> {
        let mut it = expression.into_inner();
        let name = it.next().unwrap().as_str().to_owned();

        let args = it
            .next()
            .and_then(|expr| Some(self.parse_common_arguments(expr)))
            .transpose()?;

        Ok(Filter { name, args })
    }

    fn parse_common_arguments(
        &self,
        expression: Pair<Rule>,
    ) -> Result<Vec<CommonArgument>, LiquidError> {
        expression
            .into_inner()
            .map(|expr| self.parse_common_argument(expr))
            .collect()
    }

    fn parse_common_argument(&self, expression: Pair<Rule>) -> Result<CommonArgument, LiquidError> {
        match expression.as_rule() {
            Rule::positional_argument => Ok(CommonArgument {
                value: Some(self.parse_primitive(expression.into_inner().next().unwrap())?),
                name: None,
            }),
            Rule::keyword_argument => {
                let mut it = expression.into_inner();
                let name = it.next().unwrap().as_str().to_owned();
                let value = self.parse_primitive(it.next().unwrap())?;
                Ok(CommonArgument {
                    value: Some(value),
                    name: Some(name),
                })
            }
            _ => unreachable!(),
        }
    }

    fn parse_keywords_and_symbols(
        &self,
        expression: Pair<Rule>,
    ) -> Result<Vec<CommonArgument>, LiquidError> {
        expression
            .into_inner()
            .map(|expr| self.parse_keyword_or_symbol(expr))
            .collect()
    }

    fn parse_keyword_or_symbol(
        &self,
        expression: Pair<Rule>,
    ) -> Result<CommonArgument, LiquidError> {
        match expression.as_rule() {
            Rule::positional_argument => Ok(CommonArgument {
                value: None,
                name: Some(expression.into_inner().next().unwrap().as_str().to_owned()),
            }),
            Rule::keyword_argument => {
                let mut it = expression.into_inner();
                let name = it.next().unwrap().as_str().to_owned();
                let value = self.parse_primitive(it.next().unwrap())?;
                Ok(CommonArgument {
                    value: Some(value),
                    name: Some(name),
                })
            }
            _ => unreachable!(),
        }
    }

    fn parse_inline_condition(
        &self,
        expression: Pair<Rule>,
    ) -> Result<InlineCondition, LiquidError> {
        let mut it = expression.into_inner();

        let condition = self.parse_boolean_expression(it.next().unwrap())?;
        let mut alternative: Option<Primitive> = None;
        let mut alternative_filters: Option<Vec<Filter>> = None;
        let tail_filters: Option<Vec<Filter>>;

        let pair = it.next().unwrap();

        if pair.as_rule() == Rule::alternative {
            let mut inner_it = pair.into_inner();
            alternative = Some(self.parse_primitive(inner_it.next().unwrap())?);

            alternative_filters = inner_it
                .next()
                .and_then(|expr| Some(self.parse_filters(expr)))
                .transpose()?;

            tail_filters = it
                .next()
                .and_then(|expr| Some(self.parse_filters(expr)))
                .transpose()?;
        } else {
            assert!(pair.as_rule() == Rule::tail_filters);
            tail_filters = Some(self.parse_filters(pair)?)
        }

        Ok(InlineCondition {
            expr: condition,
            alternative,
            alternative_filters,
            tail_filters,
        })
    }

    fn parse_boolean_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        self.parse_logical_or_expression(expression)
    }

    fn parse_logical_or_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        let mut it = expression.into_inner();
        let mut or_expr = self.parse_logical_and_expression(it.next().unwrap())?;

        for expr in it {
            let right = self.parse_logical_and_expression(expr)?;
            or_expr = BooleanExpression::Logical {
                left: Box::new(or_expr),
                operator: BooleanOperator::Or {},
                right: Box::new(right),
            };
        }

        Ok(or_expr)
    }

    fn parse_logical_and_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        let mut it = expression.into_inner();
        let mut and_expr = self.parse_basic_expression(it.next().unwrap())?;

        for expr in it {
            let right = self.parse_basic_expression(expr)?;
            and_expr = BooleanExpression::Logical {
                left: Box::new(and_expr),
                operator: BooleanOperator::And {},
                right: Box::new(right),
            };
        }

        Ok(and_expr)
    }

    fn parse_basic_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        match expression.as_rule() {
            Rule::logical_not => self.parse_logical_not_expression(expression),
            Rule::primitive => Ok(BooleanExpression::Primitive {
                expr: self.parse_primitive(expression)?,
            }),
            Rule::grouped_expr => self.parse_paren_expression(expression),
            Rule::compare_expr => self.parse_compare_expression(expression),
            Rule::membership_expr => self.parse_membership_expression(expression),
            _ => unreachable!(),
        }
    }

    fn parse_logical_not_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        Ok(BooleanExpression::LogicalNot {
            expr: Box::new(self.parse_basic_expression(expression.into_inner().next().unwrap())?),
        })
    }

    fn parse_paren_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        self.parse_logical_or_expression(expression.into_inner().next().unwrap())
    }

    fn parse_compare_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        let mut it = expression.into_inner();
        let left = self.parse_primitive(it.next().unwrap())?;

        let operator = match it.next().unwrap().as_str() {
            "==" => CompareOperator::Eq {},
            "!=" => CompareOperator::Ne {},
            "<>" => CompareOperator::Ne {},
            "<=" => CompareOperator::Le {},
            ">=" => CompareOperator::Ge {},
            "<" => CompareOperator::Lt {},
            ">" => CompareOperator::Gt {},
            _ => unreachable!(),
        };

        let right = self.parse_primitive(it.next().unwrap())?;

        Ok(BooleanExpression::Comparison {
            left,
            operator,
            right,
        })
    }

    fn parse_membership_expression(
        &self,
        expression: Pair<Rule>,
    ) -> Result<BooleanExpression, LiquidError> {
        let mut it = expression.into_inner();
        let left = self.parse_primitive(it.next().unwrap())?;

        let operator = match it.next().unwrap().as_str() {
            "in" => MembershipOperator::In {},
            "not in" => MembershipOperator::NotIn {},
            "contains" => MembershipOperator::Contains {},
            "not contains" => MembershipOperator::NotContains {},
            _ => unreachable!(),
        };

        let right = self.parse_primitive(it.next().unwrap())?;

        Ok(BooleanExpression::Membership {
            left,
            operator,
            right,
        })
    }

    fn parse_primitive(&self, expression: Pair<Rule>) -> Result<Primitive, LiquidError> {
        match expression.as_rule() {
            Rule::number => self.parse_number(expression),
            Rule::multiline_double_quoted => Ok(Primitive::StringLiteral {
                value: unescape_string(expression.as_str()),
            }),
            Rule::multiline_single_quoted => Ok(Primitive::StringLiteral {
                value: unescape_string(&expression.as_str().replace("\\'", "'")),
            }),
            Rule::true_literal => Ok(Primitive::TrueLiteral {}),
            Rule::false_literal => Ok(Primitive::FalseLiteral {}),
            Rule::null => Ok(Primitive::NullLiteral {}),
            Rule::range => todo!(),
            Rule::query => Ok(Primitive::Query {
                path: self.query_parser.parse(expression.into_inner())?,
            }),
            _ => unreachable!("Rule: {:#?}", expression),
        }
    }

    fn parse_number(&self, expr: Pair<Rule>) -> Result<Primitive, LiquidError> {
        if expr.as_str() == "-0" {
            return Ok(Primitive::Integer { value: 0 });
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
            Ok(Primitive::Float {
                value: n
                    .parse::<f64>()
                    .map_err(|_| LiquidError::syntax(String::from("invalid float literal")))?,
            })
        } else {
            Ok(Primitive::Integer {
                value: n
                    .parse::<f64>()
                    .map_err(|_| LiquidError::syntax(String::from("invalid integer literal")))?
                    as i64,
            })
        }
    }

    fn parse_standard_tag(
        &self,
        tag: Pair<Rule>,
        stream: &mut Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        let mut it = tag.into_inner();
        let wc = Whitespace::from_str(it.next().unwrap().as_str());
        let expr = it.next().unwrap();

        match expr.as_rule() {
            Rule::assign => self.parse_assign_tag(wc, it),
            Rule::capture => self.parse_capture_tag(wc, it, stream),
            Rule::case => self.parse_case_tag(wc, it, stream),
            Rule::cycle => self.parse_cycle_tag(wc, it),
            Rule::decrement => self.parse_decrement_tag(wc, it),
            Rule::increment => self.parse_increment_tag(wc, it),
            Rule::echo => self.parse_echo_tag(wc, it),
            Rule::for_ => self.parse_for_tag(wc, it, stream),
            _ => todo!("{:#?}", expr),
        }
    }

    fn parse_assign_tag(&self, wc: Whitespace, mut it: Pairs<Rule>) -> Result<Node, LiquidError> {
        let identifier = it.next().unwrap().as_str().to_owned();
        let expression = self.parse_filtered_expression(it.next().unwrap())?;
        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        Ok(Node::AssignTag {
            whitespace_control: WhitespaceControl {
                left: wc,
                right: wc_right,
            },
            identifier,
            expression,
        })
    }

    fn parse_capture_tag(
        &self,
        wc: Whitespace,
        mut it: Pairs<Rule>,
        stream: &mut Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        let identifier = it.next().unwrap().as_str().to_owned();
        let start_wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        let block = self.parse_named_block(stream, "capture")?;
        let end_tag = stream.next().unwrap();
        assert!(end_tag.as_rule() == Rule::end_tag);
        let mut end_it = end_tag.into_inner();
        let end_wc_left = Whitespace::from_str(end_it.next().unwrap().as_str());
        assert!(end_it.next().unwrap().as_str() == "capture");
        let end_wc_right = Whitespace::from_str(end_it.next().unwrap().as_str());
        Ok(Node::CaptureTag {
            whitespace_control: (
                WhitespaceControl {
                    left: wc,
                    right: start_wc_right,
                },
                WhitespaceControl {
                    left: end_wc_left,
                    right: end_wc_right,
                },
            ),
            identifier,
            block,
        })
    }

    fn parse_case_tag(
        &self,
        wc: Whitespace,
        mut it: Pairs<Rule>,
        stream: &mut Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        let arg = self.parse_primitive(it.next().unwrap())?;
        let start_wc_right = Whitespace::from_str(it.next().unwrap().as_str());

        if stream.peek().is_some_and(|p| p.as_rule() == Rule::content) {
            stream.next();
        }

        let mut whens: Vec<WhenTag> = Vec::new();

        while stream.peek().is_some_and(|p| self.is_tag(p, "when")) {
            let tag = stream.next().unwrap();
            whens.push(self.parse_when_tag(tag, stream)?)
        }

        let mut default: Option<ElseTag> = None;
        if stream.peek().is_some_and(|p| self.is_tag(p, "else")) {
            let mut else_it = stream.next().unwrap().into_inner();
            let else_wc_left = Whitespace::from_str(else_it.next().unwrap().as_str());
            assert!(else_it.next().unwrap().as_str() == "else");
            let else_wc_right = Whitespace::from_str(else_it.next().unwrap().as_str());
            default = Some(ElseTag {
                whitespace_control: WhitespaceControl {
                    left: else_wc_left,
                    right: else_wc_right,
                },
                block: self.parse_named_block(stream, "case")?,
            });
        }

        let end_tag = stream.next().unwrap();
        // TODO: syntax error if not end tag
        assert!(end_tag.as_rule() == Rule::end_tag);
        let mut end_it = end_tag.into_inner();
        let end_wc_left = Whitespace::from_str(end_it.next().unwrap().as_str());
        assert!(end_it.next().unwrap().as_str() == "case");
        let end_wc_right = Whitespace::from_str(end_it.next().unwrap().as_str());

        Ok(Node::CaseTag {
            whitespace_control: (
                WhitespaceControl {
                    left: wc,
                    right: start_wc_right,
                },
                WhitespaceControl {
                    left: end_wc_left,
                    right: end_wc_right,
                },
            ),
            arg,
            whens,
            default,
        })
    }

    fn parse_when_tag(
        &self,
        tag: Pair<Rule>,
        stream: &mut Pairs<Rule>,
    ) -> Result<WhenTag, LiquidError> {
        let mut it = tag.into_inner();
        let wc_left = Whitespace::from_str(it.next().unwrap().as_str());
        assert!(it.next().unwrap().as_rule() == Rule::when);
        let mut args: Vec<Primitive> = Vec::new();

        while it.peek().is_some_and(|p| p.as_rule() != Rule::WC) {
            args.push(self.parse_primitive(it.next().unwrap())?);
        }

        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        let block_end = &self.tags.get("case").unwrap().end;
        let block = self.parse_block_until(stream, block_end)?;

        Ok(WhenTag {
            whitespace_control: WhitespaceControl {
                left: wc_left,
                right: wc_right,
            },
            args,
            block,
        })
    }

    fn parse_cycle_tag(&self, wc: Whitespace, mut it: Pairs<Rule>) -> Result<Node, LiquidError> {
        let name: Option<String>;
        if it.peek().is_some_and(|p| p.as_rule() == Rule::cycle_group) {
            name = Some(it.next().unwrap().as_str().to_owned());
        } else {
            name = None;
        }

        let mut args: Vec<Primitive> = Vec::new();
        while it.peek().is_some_and(|p| p.as_rule() != Rule::WC) {
            args.push(self.parse_primitive(it.next().unwrap())?);
        }

        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());

        Ok(Node::CycleTag {
            whitespace_control: WhitespaceControl {
                left: wc,
                right: wc_right,
            },
            name,
            args,
        })
    }

    fn parse_decrement_tag(
        &self,
        wc: Whitespace,
        mut it: Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        let name = it.next().unwrap().as_str().to_owned();
        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        Ok(Node::DecrementTag {
            whitespace_control: WhitespaceControl {
                left: wc,
                right: wc_right,
            },
            name,
        })
    }

    fn parse_increment_tag(
        &self,
        wc: Whitespace,
        mut it: Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        let name = it.next().unwrap().as_str().to_owned();
        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        Ok(Node::IncrementTag {
            whitespace_control: WhitespaceControl {
                left: wc,
                right: wc_right,
            },
            name,
        })
    }

    fn parse_echo_tag(&self, wc: Whitespace, mut it: Pairs<Rule>) -> Result<Node, LiquidError> {
        let expression = self.parse_filtered_expression(it.next().unwrap())?;
        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());

        Ok(Node::EchoTag {
            whitespace_control: WhitespaceControl {
                left: wc,
                right: wc_right,
            },
            expression,
        })
    }

    fn parse_for_tag(
        &self,
        wc: Whitespace,
        mut it: Pairs<Rule>,
        stream: &mut Pairs<Rule>,
    ) -> Result<Node, LiquidError> {
        let name = it.next().unwrap().as_str().to_owned();
        let iterable = self.parse_primitive(it.next().unwrap())?;

        let mut limit: Option<Primitive> = None;
        let mut offset: Option<Primitive> = None;
        let mut reversed = false;

        let args = self.parse_keywords_and_symbols(it.next().unwrap())?;
        for arg in args {
            match arg {
                CommonArgument { name: Some(s), .. } => match s.as_str() {
                    "limit" => limit = Some(arg.value.unwrap()),
                    "offset" => offset = Some(arg.value.unwrap()),
                    "reversed" => {
                        if arg.value.is_some() {
                            return Err(LiquidError::syntax(
                                "unexpected value for symbol 'reversed'".to_string(),
                            ));
                        }
                        reversed = true
                    }
                    _ => {
                        return Err(LiquidError::syntax(format!(
                            "expected 'limit', 'offset' or 'reversed', found '{}'",
                            s
                        )))
                    }
                },
                _ => {
                    return Err(LiquidError::syntax(format!(
                        "expected 'limit', 'offset' or 'reversed', found {:#?}",
                        arg
                    )))
                }
            }
        }

        let wc_right = Whitespace::from_str(it.next().unwrap().as_str());
        let block_end = &self.tags.get("for").unwrap().end;
        let block = self.parse_block_until(stream, block_end)?;

        let mut default: Option<ElseTag> = None;
        if stream.peek().is_some_and(|p| self.is_tag(p, "else")) {
            let mut else_it = stream.next().unwrap().into_inner();
            let else_wc_left = Whitespace::from_str(else_it.next().unwrap().as_str());
            assert!(else_it.next().unwrap().as_str() == "else");
            let else_wc_right = Whitespace::from_str(else_it.next().unwrap().as_str());
            default = Some(ElseTag {
                whitespace_control: WhitespaceControl {
                    left: else_wc_left,
                    right: else_wc_right,
                },
                block: self.parse_named_block(stream, "for")?,
            });
        }

        let end_tag = stream.next().unwrap();
        assert!(end_tag.as_rule() == Rule::end_tag);
        let mut end_it = end_tag.into_inner();
        let end_wc_left = Whitespace::from_str(end_it.next().unwrap().as_str());
        assert!(end_it.next().unwrap().as_str() == "for");
        let end_wc_right = Whitespace::from_str(end_it.next().unwrap().as_str());

        Ok(Node::ForTag {
            whitespace_control: (
                WhitespaceControl {
                    left: wc,
                    right: wc_right,
                },
                WhitespaceControl {
                    left: end_wc_left,
                    right: end_wc_right,
                },
            ),
            name,
            iterable,
            limit,
            offset,
            reversed,
            block,
            default,
        })
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
            Rule::child_segment | Rule::implicit_root_segment => Segment::Child {
                selectors: self.parse_segment_inner(segment.into_inner().next().unwrap())?,
            },
            Rule::descendant_segment => Segment::Recursive {
                selectors: self.parse_segment_inner(segment.into_inner().next().unwrap())?,
            },
            Rule::name_segment | Rule::implicit_root_name_segment | Rule::index_segment => {
                Segment::Child {
                    selectors: vec![self.parse_selector(segment.into_inner().next().unwrap())?],
                }
            }
            Rule::EOI => Segment::Eoi {},
            _ => unreachable!("Rule: {:#?}", segment),
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

pub struct TagMeta {
    pub block: bool,
    pub end: HashSet<String>,
}

pub fn standard_tags() -> HashMap<String, TagMeta> {
    // TODO: need to know set of end tag names for each block tag
    let mut tags = HashMap::new();

    tags.insert(
        "assign".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    let mut end_capture = HashSet::new();
    end_capture.insert("capture".to_owned());
    tags.insert(
        "capture".to_owned(),
        TagMeta {
            block: true,
            end: end_capture,
        },
    );

    let mut end_case = HashSet::new();
    end_case.insert("case".to_owned());
    end_case.insert("when".to_owned());
    end_case.insert("else".to_owned());
    tags.insert(
        "case".to_owned(),
        TagMeta {
            block: true,
            end: end_case,
        },
    );

    tags.insert(
        "cycle".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags.insert(
        "decrement".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags.insert(
        "increment".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags.insert(
        "echo".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    let mut end_for = HashSet::new();
    end_for.insert("for".to_owned());
    end_for.insert("else".to_owned());
    tags.insert(
        "for".to_owned(),
        TagMeta {
            block: true,
            end: end_for,
        },
    );

    tags.insert(
        "break".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags.insert(
        "continue".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    let mut end_if = HashSet::new();
    end_if.insert("if".to_owned());
    end_if.insert("elsif".to_owned());
    end_if.insert("elif".to_owned());
    end_if.insert("else".to_owned());
    tags.insert(
        "if".to_owned(),
        TagMeta {
            block: true,
            end: end_if,
        },
    );

    let mut end_unless = HashSet::new();
    end_unless.insert("unless".to_owned());
    end_unless.insert("elsif".to_owned());
    end_unless.insert("elif".to_owned());
    end_unless.insert("else".to_owned());
    tags.insert(
        "unless".to_owned(),
        TagMeta {
            block: true,
            end: end_unless,
        },
    );

    tags.insert(
        "include".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags.insert(
        "render".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags.insert(
        "liquid".to_owned(),
        TagMeta {
            block: false,
            end: HashSet::new(),
        },
    );

    tags
}
