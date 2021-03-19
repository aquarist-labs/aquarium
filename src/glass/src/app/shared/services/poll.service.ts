import { Injectable } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { MonoTypeOperatorFunction, timer } from 'rxjs';
import { last, scan, switchMapTo, takeWhile, tap } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';

@Injectable({
  providedIn: 'root'
})
export class PollService {
  constructor() {}

  /**
   * Poll the specified service until the given callback function
   * returns `false`.
   *
   * @param isActive The callback function. Must return `false` to
   *   stop polling.
   * @param maxAttempts The maximum number of attempts. Defaults
   *   to `Infinity`.
   * @param errorMessage The error message thrown when the maximum
   *   number of attempts have been reached.
   * @param interval The poll interval in milliseconds.
   * @param retLastResult Return the last result? Defaults to `true`.
   */
  poll<T>(
    isActive: (res: T) => boolean,
    maxAttempts: number = Infinity,
    errorMessage: string = TEXT('Failed to fetch data'),
    interval: number = 5000,
    retLastResult: boolean = true
  ): MonoTypeOperatorFunction<T> {
    return (source$) => {
      const poll$ = timer(0, interval).pipe(
        scan((attempts) => ++attempts, 0),
        tap(this.checkAttempts(maxAttempts, errorMessage)),
        switchMapTo(source$),
        takeWhile(isActive, true)
      );

      return retLastResult ? poll$.pipe(last()) : poll$;
    };
  }

  private checkAttempts(maxAttempts: number, errorMessage: string) {
    return (attemptsCount: number) => {
      if (attemptsCount > maxAttempts) {
        throw new Error(translate(errorMessage));
      }
    };
  }
}
