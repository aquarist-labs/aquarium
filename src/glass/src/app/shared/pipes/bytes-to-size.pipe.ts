import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'bytesToSize'
})
export class BytesToSizePipe implements PipeTransform {
  transform(bytes: number): string {
    if (bytes === 0) {
      return '0 Bytes';
    }

    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const factor = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(factor));
    return Math.round(bytes / Math.pow(factor, i)) + ' ' + sizes[i];
  }
}
