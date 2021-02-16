import { Pipe, PipeTransform } from '@angular/core';
import * as _ from 'lodash';

@Pipe({
  name: 'sortBy'
})
export class SortByPipe implements PipeTransform {
  transform(value: Record<string, any>[], iterates: string[]): Record<string, any>[] {
    return _.sortBy(value, iterates);
  }
}
