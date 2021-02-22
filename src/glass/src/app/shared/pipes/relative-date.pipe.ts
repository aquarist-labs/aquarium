import { Pipe, PipeTransform } from '@angular/core';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import * as _ from 'lodash';

dayjs.extend(relativeTime);

@Pipe({
  name: 'relativeDate',
  pure: false
})
export class RelativeDatePipe implements PipeTransform {
  /**
   * @param date The date to process. This can be a Unix timestamp in
   *   seconds since 1. Jan 1970, a string or Date object. If it is a
   *   number < 0, then the number of seconds will be subtracted from
   *   `now`.
   * @param withoutSuffix If you pass true, you can get the value
   *   without the suffix. Defaults to `false`.
   */
  transform(value: number | string | Date | undefined, withoutSuffix: boolean = false): string {
    let date: dayjs.Dayjs;
    if (_.isNumber(value)) {
      if (value < 0) {
        date = dayjs().add(value, 'seconds');
      } else {
        date = dayjs.unix(value);
      }
    } else {
      date = dayjs(value);
    }
    return date.fromNow(withoutSuffix);
  }
}
