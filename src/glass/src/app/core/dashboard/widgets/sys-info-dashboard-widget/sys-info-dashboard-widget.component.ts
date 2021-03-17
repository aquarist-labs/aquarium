import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Facts, OrchService } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-sys-info-dashboard-widget',
  templateUrl: './sys-info-dashboard-widget.component.html',
  styleUrls: ['./sys-info-dashboard-widget.component.scss']
})
export class SysInfoDashboardWidgetComponent {
  data: Facts = {} as Facts;
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

  constructor(private bytesToSizePipe: BytesToSizePipe, private orchService: OrchService) {}

  valueFormatting(c: any) {
    return this.bytesToSizePipe.transform(c);
  }

  updateData($data: Facts) {
    this.data = $data;
  }

  loadData(): Observable<Facts> {
    return this.orchService.facts().pipe(
      map((facts: Facts) => {
        this.memoryChartData = [
          {
            name: translate(TEXT('Used')),
            value: facts.memory_total_kb * 1024 - facts.memory_free_kb * 1024
          },
          { name: translate(TEXT('Free')), value: facts.memory_free_kb * 1024 }
        ];
        /* eslint-disable @typescript-eslint/naming-convention */
        const load_1min = Math.floor(facts.cpu_load['1min'] * 100);
        const load_5min = Math.floor(facts.cpu_load['5min'] * 100);
        const load_15min = Math.floor(facts.cpu_load['15min'] * 100);
        this.cpuLoadChartData = [
          { name: translate(TEXT('1min')), value: `${load_1min}%` },
          { name: translate(TEXT('5min')), value: `${load_5min}%` },
          { name: translate(TEXT('15min')), value: `${load_15min}%` }
        ];
        // Modify the uptime value to allow the `relativeDate` pipe
        // to calculate the correct time to display.
        facts.system_uptime = facts.system_uptime * -1;
        return facts;
      })
    );
  }
}
