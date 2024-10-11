# Type system

## Primitives

- Array / list / sequence
- Hash / dict / mapping
- plus literals ...

### Literals

- true
- false
- null (aka nil)
- range
- string
- int
- float

and

- query

### Keywords

- empty
- blank

### Implicit type conversion

Tag and filter arguments are implicitly coerced into a suitable type according to the following rules.

TODO: preamble about matching types
TODO: preamble about resolving singular queries
TODO: undefined is falsy
TODO: if argument is a drop

1. If a string argument is expected

   a. and the argument is a primitive value, the argument value is converted to its string representation.

   b. and the argument is a singular query, the query result value is converted to its string representation.

   c. and the argument is a non-singular query, it is an error condition.

2. If a number is expected,

   a. and the argument is a string, the argument is converted to its equivalent int or float.

   b. otherwise it is an error condition

3. If a Boolean is expected

   a. and the argument is false, null, nil or undefined, the argument is false

   b. otherwise the argument is true, even for empty containers.

4. If an array is expected

   TODO: flatten arrays

   a. and the argument is a string, the string is converted to an array of unicode "characters".

   b. and the argument is a mapping, the mapping is converted to an array of key/value pairs.

   c. otherwise the argument is converted to a single element array with the argument value as the only element.

5. If a range is expected

   a. and the argument is not a range object, it is an error condition.

6. If a mapping is expected

   a. and the argument is not a mapping, it is an error condition.

## Array filters

### Input iterator

- compact
- concat (arg responds to to_ary)
- join
- map
- reverse
- sort
- sort_natural
- sum
- uniq
- where

### Responds to

- first
- last
