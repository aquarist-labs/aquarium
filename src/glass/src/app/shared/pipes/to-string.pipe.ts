import { Pipe, PipeTransform } from '@angular/core';
import * as _ from 'lodash';

@Pipe({
  name: 'toString'
})
export class ToStringPipe implements PipeTransform {
  transform(value: unknown): string {
    return _.toString(value);
  }
}
