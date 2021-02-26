import { Injectable } from '@angular/core';
import { MonoTypeOperatorFunction, timer } from 'rxjs';
import { last, scan, switchMapTo, takeWhile, tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class PollService {
  constructor() {}

  poll<T>(
    isActive: (res: T) => boolean,
    maxAttempts: number = Infinity,
    errorMessage: string = 'Failed to fetch data',
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
        throw new Error(errorMessage);
      }
    };
  }
}
