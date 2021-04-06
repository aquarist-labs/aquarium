import { Component } from '@angular/core';
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
  chartDataWrite: any[] = [];
  chartDataRead: any[] = [];

  constructor(public service: StatusService) {}

  updateChartData($data: ClientIO) {
    this.chartDataWrite = this.mapServiceRate($data, 'write');
    this.chartDataRead = this.mapServiceRate($data, 'read');
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
