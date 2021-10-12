export type Constraint = {
  operator:
    | 'and'
    | 'or'
    | 'not'
    | 'lt'
    | 'le'
    | 'ne'
    | 'eq'
    | 'ge'
    | 'gt'
    | 'in'
    | 'z'
    | 'n'
    | 'length'
    | 'truthy'
    | 'falsy'
    | 'startsWith'
    | 'endsWith'
    | 'regexp';
  arg0: Constraint | ConstraintProperty | boolean | number | string | Array<number | string>;
  arg1?: Constraint | boolean | number | string | Array<number | string>;
};

export type ConstraintProperty = {
  // The path of the property, e.g. 'foo' or 'foo.bar.baz'.
  prop: string;
};
