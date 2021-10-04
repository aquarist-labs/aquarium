import { Pipe, PipeTransform } from '@angular/core';

import { bytesToSize } from '~/app/functions.helper';

@Pipe({
  name: 'bytesToSize'
})
export class BytesToSizePipe implements PipeTransform {
  transform(value: null | number | string): string {
    return bytesToSize(value);
  }
}
