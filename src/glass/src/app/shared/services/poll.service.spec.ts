import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { TestScheduler } from 'rxjs/testing';

import { PollService } from './poll.service';

describe('PollServiceService', () => {
  let service: PollService;
  let scheduler: TestScheduler;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PollService);

    scheduler = new TestScheduler((actual, expected) => {
      expect(actual).toEqual(expected);
    });
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should poll a service 3 times and raise an error', () => {
    scheduler.run((helpers) => {
      const source$ = of(1);
      const result$ = source$.pipe(service.poll(() => true, 3, undefined, 2, false));
      const expected = '1-1-1-#';

      helpers.expectObservable(result$).toBe(expected, { 1: 1 }, Error('Failed to fetch data'));
    });
  });

  it('should poll a service 3 times and raise a custom error', () => {
    scheduler.run((helpers) => {
      const source$ = of(1);
      const result$ = source$.pipe(service.poll(() => true, 3, 'Test error message', 2, false));
      const expected = '1-1-1-#';

      helpers.expectObservable(result$).toBe(expected, { 1: 1 }, Error('Test error message'));
    });
  });

  it('should return the last result only', () => {
    scheduler.run((helpers) => {
      const source$ = helpers.cold('1-2-3-4-5-6');
      const result$ = source$.pipe(service.poll((res) => +res !== 6));
      const expected = '----------(6|)';
      helpers.expectObservable(result$).toBe(expected);
    });
  });
});
