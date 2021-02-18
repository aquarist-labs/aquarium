import { Pipe, PipeTransform } from '@angular/core';
import * as _ from 'lodash';

@Pipe({
  name: 'bytesToSize'
})
export class BytesToSizePipe implements PipeTransform {
  transform(value: null | number | string): string {
    if (_.isNull(value) || [0, '0', ''].includes(value)) {
      return '0 Bytes';
    }
    const bytes = _.toNumber(value);
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const factor = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(factor));
    return Math.round(bytes / Math.pow(factor, i)) + ' ' + sizes[i];
  }
}
