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

  constructor(public service: StatusService, private bytesToSizePipe: BytesToSizePipe) {}

  updateChartData($data: ClientIO) {
    this.chartDataWrite = this.mapServiceRate($data, 'write');
    this.chartDataRead = this.mapServiceRate($data, 'read');
  }

  valueFormatting(c: any) {
    return this.bytesToSizePipe.transform(c) + '/s';
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
