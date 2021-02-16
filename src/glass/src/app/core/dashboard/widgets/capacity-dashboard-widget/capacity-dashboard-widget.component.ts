import { Component, OnDestroy, OnInit } from '@angular/core';
import { Chart } from 'chart.js';
import * as _ from 'lodash';
import { Observable, of, Subscription } from 'rxjs';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';

@Component({
  selector: 'glass-capacity-dashboard-widget',
  templateUrl: './capacity-dashboard-widget.component.html',
  styleUrls: ['./capacity-dashboard-widget.component.scss']
})
export class CapacityDashboardWidgetComponent
  extends AbstractDashboardWidget<number[]>
  implements OnInit, OnDestroy {
  chart?: Chart;
  data: number[] = [];

  protected subscription: Subscription = new Subscription();

  constructor() {
    super();
    this.subscription = this.loadDataEvent.subscribe(() => {
      if (this.chart) {
        _.set(this.chart, 'data.datasets.0.data', this.data);
        this.chart.update();
      }
    });
  }

  ngOnInit(): void {
    super.ngOnInit();
    this.chart = new Chart('chart', {
      type: 'doughnut',
      data: {
        labels: ['Available', 'Used'],
        datasets: [
          {
            data: this.data,
            backgroundColor: ['#ffcd56', '#ff9f40']
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        legend: {
          position: 'bottom'
        }
      }
    });
  }

  ngOnDestroy(): void {
    super.ngOnDestroy();
    this.subscription.unsubscribe();
  }

  loadData(): Observable<number[]> {
    const used = _.random(0, 100);
    const available = 100 - used;
    return of([available, used]);
  }
}
