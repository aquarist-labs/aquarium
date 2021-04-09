import { Pipe, PipeTransform } from '@angular/core';
import * as _ from 'lodash';

@Pipe({
  name: 'map'
})
export class MapPipe implements PipeTransform {
  transform(value: any, map: Record<any, any>): any {
    return _.get(map, value, value);
  }
}
