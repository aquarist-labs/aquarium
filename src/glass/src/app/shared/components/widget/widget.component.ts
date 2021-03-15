import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import * as _ from 'lodash';
import { EMPTY, Observable, Subscription } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

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

  error = false;
  loading = false;
  firstLoadComplete = false;
  data?: any;

  private loadingWithoutError = true;
  private refreshDataSubscription?: Subscription;

  // eslint-disable-next-line @typescript-eslint/naming-convention
  private readonly RELOAD = 15000;

  ngOnInit(): void {
    this.refreshData();
  }

  ngOnDestroy(): void {
    this.refreshDataSubscription?.unsubscribe();
  }

  private refreshData(): void {
    if (!this.loadData) {
      throw new Error('loadData attribute not set');
    }
    this.loading = true;
    this.loadingWithoutError = true;
    this.refreshDataSubscription = this.loadData()
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
          this.refreshDataSubscription?.unsubscribe();
          if (this.RELOAD > 0) {
            setTimeout(() => {
              this.refreshData();
            }, this.RELOAD);
          }
          this.loading = false;
        })
      )
      .subscribe((data) => {
        this.data = data;
        this.loadDataEvent.emit(data);
      });
  }
}
