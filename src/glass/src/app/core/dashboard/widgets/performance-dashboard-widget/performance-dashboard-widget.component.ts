import { Component, ViewChild } from '@angular/core';
import { GaugeComponent } from '@swimlane/ngx-charts';
import * as _ from 'lodash';
import { Observable } from 'rxjs';

import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { ClientIO, StatusService } from '~/app/shared/services/api/status.service';

@Component({
  selector: 'glass-performance-dashboard-widget',
  templateUrl: './performance-dashboard-widget.component.html',
  styleUrls: ['./performance-dashboard-widget.component.scss']
})
export class PerformanceDashboardWidgetComponent {
  @ViewChild('read', { static: true })
  readChart!: GaugeComponent;
  @ViewChild('write', { static: true })
  writeChart!: GaugeComponent;

  sizeUpdated = false;

  chartDataWrite: any[] = [];
  chartDataRead: any[] = [];

  constructor(public service: StatusService) {}

  updateChartData($data: ClientIO) {
    this.chartDataWrite = this.mapServiceRate($data, 'write');
    this.chartDataRead = this.mapServiceRate($data, 'read');

    // This is a somewhat dumb workaround to force the charts to adapt
    // their size to the parent container. This is caused by the change
    // detection strategy 'ChangeDetectionStrategy.OnPush' of the chart.
    // The size of the charts is otherwise rendered with 600x400 pixels
    // and only updated the second time the data is loaded (which is 15
    // seconds by default).
    if (!this.sizeUpdated) {
      setTimeout(() => {
        this.readChart.update();
        this.writeChart.update();
        this.sizeUpdated = true;
      });
    }
  }

  valueFormatting(c: any) {
    // Note, this implementation is by intention, do NOT use code like
    // 'valueFormatting.bind(this)', otherwise this method is called
    // over and over again because Angular CD seems to assume something
    // has been changed.
    const pipe = new BytesToSizePipe();
    return pipe.transform(c) + '/s';
  }

  loadData(): Observable<ClientIO> {
    return this.service.clientIO();
  }

  private mapServiceRate(
    $data: ClientIO,
    rate: 'read' | 'write'
  ): { name: string; value: number }[] {
    _.orderBy($data.services, ['io_rate.rate'], ['desc']);
    return _.take($data.services, 5).map((s) => ({
      name: `${s.service_name} (${s.service_type})`,
      value: s.io_rate[rate]
    }));
  }
}
