import { Injectable } from '@angular/core';
import * as _ from 'lodash';

import { Constraint, ConstraintProperty } from '~/app/shared/models/constraint.type';

@Injectable({
  providedIn: 'root'
})
export class ConstraintService {
  /**
   * Evaluate the constraint.
   *
   * @param constraint The constraint to process.
   * @param object The data to be used.
   * @return Returns `true` if the constraint is fulfilled,
   *   otherwise `false`.
   */
  public static test(constraint: Constraint, data: Record<any, any>): boolean {
    // eslint-disable-next-line no-underscore-dangle
    const _test = (node: Constraint | any, _data: Record<any, any>): any => {
      let result: any = false;
      if (_.isPlainObject(node)) {
        if (_.has(node, 'prop')) {
          node = node as ConstraintProperty;
          result = _.get(_data, node.prop);
        } else if (_.has(node, 'operator')) {
          let arg0;
          let arg1;
          node = node as Constraint;
          switch (node.operator) {
            case 'and':
              result = _test(node.arg0, _data) && _test(node.arg1, _data);
              break;
            case 'or':
              result = _test(node.arg0, _data) || _test(node.arg1, _data);
              break;
            case 'not':
              result = !_test(node.arg0, _data);
              break;
            case 'lt':
              result = _test(node.arg0, _data) < _test(node.arg1, _data);
              break;
            case 'le':
              result = _test(node.arg0, _data) <= _test(node.arg1, _data);
              break;
            case 'ne':
              result = _test(node.arg0, _data) !== _test(node.arg1, _data);
              break;
            case 'eq':
              result = _test(node.arg0, _data) === _test(node.arg1, _data);
              break;
            case 'ge':
              result = _test(node.arg0, _data) >= _test(node.arg1, _data);
              break;
            case 'gt':
              result = _test(node.arg0, _data) > _test(node.arg1, _data);
              break;
            case 'in':
              arg0 = _test(node.arg0, _data);
              arg1 = _test(node.arg1, _data);
              if (_.isString(arg1)) {
                result = (arg1 as string).search(arg0) !== -1;
              } else {
                result = -1 !== _.indexOf(arg1, arg0);
              }
              break;
            case 'z':
              result = _.isEmpty(_test(node.arg0, _data));
              break;
            case 'n':
              result = !_.isEmpty(_test(node.arg0, _data));
              break;
            case 'length':
              arg0 = _test(node.arg0, _data);
              result = _.get(arg0, 'length', 0);
              break;
            case 'truthy':
              result = _.includes(['yes', 'y', 'true', true, 1], _test(node.arg0, _data));
              break;
            case 'falsy':
              result = _.includes(
                ['no', 'n', 'false', false, 0, undefined, null, NaN, ''],
                _test(node.arg0, _data)
              );
              break;
            case 'startsWith':
              result = _.startsWith(_test(node.arg0, _data), _test(node.arg1, _data));
              break;
            case 'endsWith':
              result = _.endsWith(_test(node.arg0, _data), _test(node.arg1, _data));
              break;
            case 'regexp':
              arg0 = _test(node.arg0, _data);
              arg1 = _test(node.arg1, _data);
              result = RegExp(arg1 as string).exec(arg0) !== null;
              break;
          }
        }
      } else {
        result = node;
      }
      return result;
    };
    return _test(constraint, data);
  }

  /**
   * Determine the properties involved in the given constraint.
   *
   * @param constraint The constraint to process.
   * @return Returns a list of properties.
   */
  static getProps(constraint: Constraint): string[] {
    // eslint-disable-next-line no-underscore-dangle
    const _getProps = (node: Constraint | any): string[] => {
      let result = [];
      if (_.isPlainObject(node)) {
        if (_.has(node, 'prop')) {
          node = node as ConstraintProperty;
          result.push(node.prop);
        } else if (_.has(node, 'operator')) {
          node = node as Constraint;
          switch (node.operator) {
            case 'and':
            case 'or':
            case 'lt':
            case 'le':
            case 'ne':
            case 'eq':
            case 'ge':
            case 'gt':
            case 'startsWith':
            case 'endsWith':
            case 'regexp':
              result = _.concat(_getProps(node.arg0), _getProps(node.arg1));
              break;
            case 'not':
            case 'z':
            case 'n':
            case 'in':
            case 'length':
            case 'truthy':
            case 'falsy':
              result = _getProps(node.arg0);
              break;
          }
        }
      }
      return result;
    };
    return _.uniq(_getProps(constraint));
  }
}
