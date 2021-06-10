import { Component } from '@angular/core';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { ServicesService, ServiceStorage } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-services-utilization-dashboard-widget',
  templateUrl: './services-utilization-dashboard-widget.component.html',
  styleUrls: ['./services-utilization-dashboard-widget.component.scss']
})
export class ServicesUtilizationDashboardWidgetComponent {
  chartData: any[] = [];
  colorScheme = {
    domain: ['#00739c', '#fa9334', '#b54236', '#1c445c', '#00aab4']
  };

  constructor(private servicesService: ServicesService) {}

  loadData(): Observable<Array<ServiceStorage>> {
    return this.servicesService.stats().pipe(
      map((data: Record<string, ServiceStorage>): ServiceStorage[] => {
        let result: ServiceStorage[] = _.values(data);
        result = _.orderBy(result, ['utilization'], ['desc']);
        return _.map(_.take(result, 5), (record) => {
          record.utilization = parseFloat(record.utilization.toFixed(2));
          return record;
        });
      })
    );
  }

  updateChartData(data: ServiceStorage[]) {
    this.chartData = _.map(data, (serviceStorage: ServiceStorage) => ({
      name: serviceStorage.name,
      value: serviceStorage.utilization
    }));
  }

  dataLabelFormatting(value: number): string {
    return `${(value * 100).toFixed(2)}%`;
  }
}
