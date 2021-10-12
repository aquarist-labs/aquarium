import { TestBed } from '@angular/core/testing';

import { ConstraintService } from '~/app/shared/services/constraint.service';

describe('ConstraintService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  it('should test (1)', () => {
    const result = ConstraintService.test(
      {
        operator: 'lt',
        arg0: { prop: 'foo' },
        arg1: 10
      },
      { foo: 5 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (2)', () => {
    const result = ConstraintService.test(
      {
        operator: 'le',
        arg0: { prop: 'foo' },
        arg1: 5
      },
      { foo: 5 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (3)', () => {
    const result = ConstraintService.test(
      {
        operator: 'eq',
        arg0: { prop: 'foo' },
        arg1: 'xyz'
      },
      { foo: 'xyz' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (4)', () => {
    const result = ConstraintService.test(
      {
        operator: 'ge',
        arg0: { prop: 'foo' },
        arg1: 10
      },
      { foo: 10 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (5)', () => {
    const result = ConstraintService.test(
      {
        operator: 'gt',
        arg0: { prop: 'foo' },
        arg1: 5
      },
      { foo: 10 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (6)', () => {
    const result = ConstraintService.test(
      {
        operator: 'in',
        arg0: { prop: 'bar' },
        arg1: 'foo xyz bar'
      },
      { bar: 'xy' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (7)', () => {
    const result = ConstraintService.test(
      {
        operator: 'in',
        arg0: { prop: 'bar' },
        arg1: 'xxx'
      },
      { bar: 'xy' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (8)', () => {
    const result = ConstraintService.test(
      {
        operator: 'z',
        arg0: { prop: 'bar' }
      },
      { bar: '' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (9)', () => {
    const result = ConstraintService.test(
      {
        operator: 'z',
        arg0: { prop: 'bar' }
      },
      { bar: 'xyz' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (10)', () => {
    const result = ConstraintService.test(
      {
        operator: 'n',
        arg0: { prop: 'bar' }
      },
      { bar: 'xyz' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (11)', () => {
    const result = ConstraintService.test(
      {
        operator: 'n',
        arg0: { prop: 'bar' }
      },
      { bar: '' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (12)', () => {
    const result = ConstraintService.test(
      {
        operator: 'eq',
        arg0: {
          operator: 'length',
          arg0: { prop: 'baz' }
        },
        arg1: 4
      },
      { baz: 'abcd' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (13)', () => {
    const result = ConstraintService.test(
      {
        operator: 'eq',
        arg0: {
          operator: 'length',
          arg0: { prop: 'baz' }
        },
        arg1: 4
      },
      { baz: 'abcdefg' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (14)', () => {
    const result = ConstraintService.test(
      {
        operator: 'and',
        arg0: {
          operator: 'eq',
          arg0: { prop: 'bar' },
          arg1: 4
        },
        arg1: {
          operator: 'ne',
          arg0: { prop: 'baz' },
          arg1: 'y'
        }
      },
      { bar: 4, baz: 'x' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (15)', () => {
    const result = ConstraintService.test(
      {
        operator: 'or',
        arg0: {
          operator: 'eq',
          arg0: { prop: 'bar' },
          arg1: 4
        },
        arg1: {
          operator: 'gt',
          arg0: { prop: 'baz' },
          arg1: 10
        }
      },
      { bar: 5, baz: 15 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (16)', () => {
    const result = ConstraintService.test(
      {
        operator: 'not',
        arg0: {
          operator: 'eq',
          arg0: { prop: 'bar' },
          arg1: 4
        }
      },
      { bar: 4 }
    );
    expect(result).toBeFalsy();
  });

  it('should test (17)', () => {
    const result = ConstraintService.test(
      {
        operator: 'ge',
        arg0: { prop: 'foo' },
        arg1: 10
      },
      { foo: 9 }
    );
    expect(result).toBeFalsy();
  });

  it('should test (18)', () => {
    const result = ConstraintService.test(
      {
        operator: 'gt',
        arg0: { prop: 'foo' },
        arg1: 10
      },
      { foo: 10 }
    );
    expect(result).toBeFalsy();
  });

  it('should test (19)', () => {
    const result = ConstraintService.test(
      {
        operator: 'in',
        arg0: { prop: 'bar' },
        arg1: [1, 2, 3, 4]
      },
      { bar: 5 }
    );
    expect(result).toBeFalsy();
  });

  it('should test (20)', () => {
    const result = ConstraintService.test(
      {
        operator: 'truthy',
        arg0: { prop: 'foo' }
      },
      { foo: 1 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (21)', () => {
    const result = ConstraintService.test(
      {
        operator: 'truthy',
        arg0: { prop: 'foo' }
      },
      { foo: true }
    );
    expect(result).toBeTruthy();
  });

  it('should test (22)', () => {
    const result = ConstraintService.test(
      {
        operator: 'truthy',
        arg0: { prop: 'foo' }
      },
      { foo: 'yes' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (23)', () => {
    const result = ConstraintService.test(
      {
        operator: 'truthy',
        arg0: { prop: 'foo' }
      },
      { foo: 'no' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (24)', () => {
    const result = ConstraintService.test(
      {
        operator: 'falsy',
        arg0: { prop: 'foo' }
      },
      { foo: 0 }
    );
    expect(result).toBeTruthy();
  });

  it('should test (25)', () => {
    const result = ConstraintService.test(
      {
        operator: 'falsy',
        arg0: { prop: 'foo' }
      },
      { foo: false }
    );
    expect(result).toBeTruthy();
  });

  it('should test (26)', () => {
    const result = ConstraintService.test(
      {
        operator: 'falsy',
        arg0: { prop: 'foo' }
      },
      { foo: 'n' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (27)', () => {
    const result = ConstraintService.test(
      {
        operator: 'falsy',
        arg0: { prop: 'foo' }
      },
      { foo: 'yes' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (28)', () => {
    const result = ConstraintService.test(
      {
        operator: 'startsWith',
        arg0: { prop: 'foo' },
        arg1: '123'
      },
      { foo: '123456' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (29)', () => {
    const result = ConstraintService.test(
      {
        operator: 'startsWith',
        arg0: { prop: 'foo' },
        arg1: '123'
      },
      { foo: 'abcdefg' }
    );
    expect(result).toBeFalsy();
  });

  it('should test (30)', () => {
    const result = ConstraintService.test(
      {
        operator: 'endsWith',
        arg0: { prop: 'foo' },
        arg1: '456'
      },
      { foo: '123456' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (31)', () => {
    const result = ConstraintService.test(
      {
        operator: 'endsWith',
        arg0: { prop: 'foo.bar' },
        arg1: '123'
      },
      { foo: { bar: 'abcdefg' } }
    );
    expect(result).toBeFalsy();
  });

  it('should test (32)', () => {
    const result = ConstraintService.test(
      {
        operator: 'regexp',
        arg0: { prop: 'foo' },
        arg1: '^[\\d]+\\S+$'
      },
      { foo: '123abc' }
    );
    expect(result).toBeTruthy();
  });

  it('should test (33)', () => {
    const result = ConstraintService.test(
      {
        operator: 'regexp',
        arg0: { prop: 'foo' },
        arg1: '^[\\d]+\\S+$'
      },
      { foo: 'abc123' }
    );
    expect(result).toBeFalsy();
  });

  it('should get properties (1)', () => {
    const result = ConstraintService.getProps({
      operator: 'and',
      arg0: { operator: 'eq', arg0: { prop: 'prop1' }, arg1: 'foo' },
      arg1: {
        operator: 'or',
        arg0: { operator: 'eq', arg0: { prop: 'prop2' }, arg1: 'xyz' },
        arg1: { operator: 'ne', arg0: { prop: 'prop3' }, arg1: 'bar' }
      }
    });
    expect(result).toEqual(['prop1', 'prop2', 'prop3']);
  });
});
