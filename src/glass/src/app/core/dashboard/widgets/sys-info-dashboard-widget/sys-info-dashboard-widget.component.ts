import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Facts, OrchService } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-sys-info-dashboard-widget',
  templateUrl: './sys-info-dashboard-widget.component.html',
  styleUrls: ['./sys-info-dashboard-widget.component.scss']
})
export class SysInfoDashboardWidgetComponent extends AbstractDashboardWidget<Facts> {
  memoryChartData: any[] = [];
  memoryChartColorScheme = {
    // EOS colors: [$eos-bc-red-500, $eos-bc-green-500]
    domain: ['#dc3545', '#30ba78']
  };
  cpuLoadChartData: any[] = [];
  cpuLoadColorScheme = {
    // EOS colors: [$eos-bc-yellow-100, $eos-bc-yellow-500, $eos-bc-yellow-900]
    domain: ['#ffecb5', '#ffc107', '#ff9e02']
  };

  constructor(private bytesToSizePipe: BytesToSizePipe, private orchService: OrchService) {
    super();
  }

  valueFormatting(c: any) {
    return this.bytesToSizePipe.transform(c);
  }

  loadData(): Observable<Facts> {
    return this.orchService.facts().pipe(
      map((facts: Facts) => {
        this.memoryChartData = [
          { name: 'Used', value: facts.memory_total_kb * 1024 - facts.memory_free_kb * 1024 },
          { name: 'Free', value: facts.memory_free_kb * 1024 }
        ];
        this.cpuLoadChartData = [
          { name: '1min', value: facts.cpu_load['1min'] },
          { name: '5min', value: facts.cpu_load['5min'] },
          { name: '15min', value: facts.cpu_load['15min'] }
        ];
        // Modify the uptime value to allow the `relativeDate` pipe
        // to calculate the correct time to display.
        facts.system_uptime = facts.system_uptime * -1;
        return facts;
      })
    );
  }
}
