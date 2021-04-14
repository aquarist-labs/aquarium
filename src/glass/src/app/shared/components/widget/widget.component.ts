import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import * as _ from 'lodash';
import { EMPTY, Observable, Subscription, timer } from 'rxjs';
import { catchError, finalize, take } from 'rxjs/operators';

export type WidgetAction = {
  icon: string;
  name: string;
  action: () => void;
};

@Component({
  selector: 'glass-widget',
  templateUrl: './widget.component.html',
  styleUrls: ['./widget.component.scss']
})
export class WidgetComponent implements OnInit, OnDestroy {
  @Output()
  readonly loadDataEvent = new EventEmitter<any>();

  @Input()
  title = '';
  @Input()
  loadData?: () => Observable<any>;
  @Input()
  actionMenu?: WidgetAction[];

  error = false;
  loading = false;
  firstLoadComplete = false;
  data?: any;

  private loadingWithoutError = true;
  private loadDataSubscription?: Subscription;
  private timerSubscription?: Subscription;

  private readonly reloadTime = 15000;

  ngOnInit(): void {
    this.reload();
  }

  ngOnDestroy(): void {
    this.loadDataSubscription?.unsubscribe();
    this.timerSubscription?.unsubscribe();
  }

  reload(): void {
    if (!this.loadData) {
      throw new Error('loadData attribute not set');
    }
    this.loading = true;
    this.loadingWithoutError = true;
    this.loadDataSubscription = this.loadData()
      .pipe(
        // @ts-ignore
        catchError((err) => {
          if (_.isFunction(err.preventDefault)) {
            err.preventDefault();
          }
          this.loadingWithoutError = false;
          return EMPTY;
        }),
        finalize(() => {
          this.error = !this.loadingWithoutError;
          this.firstLoadComplete = this.loadingWithoutError;
          if (this.reloadTime > 0) {
            this.timerSubscription = timer(this.reloadTime)
              .pipe(take(1))
              .subscribe(() => this.reload());
          }
          this.loading = false;
        }),
        take(1)
      )
      .subscribe((data) => {
        this.data = data;
        this.loadDataEvent.emit(data);
      });
  }
}
