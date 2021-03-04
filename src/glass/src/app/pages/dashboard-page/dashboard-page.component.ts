import { Component, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';

import { DashboardWidgetConfig } from '~/app/shared/models/dashboard-widget.model';
import { LocalStorageService } from '~/app/shared/services/local-storage.service';

@Component({
  selector: 'glass-dashboard-page',
  templateUrl: './dashboard-page.component.html',
  styleUrls: ['./dashboard-page.component.scss']
})
export class DashboardPageComponent implements OnInit {
  enabled: string[] = ['health', 'capacity', 'services', 'volumes', 'sysInfo', 'hosts'];

  // New dashboard widgets must be added here. Don't forget to enhance
  // the template to render the new widget.
  readonly widgets: DashboardWidgetConfig[] = [
    {
      id: 'health',
      title: TEXT('Health')
    },
    {
      id: 'capacity',
      title: TEXT('Capacity')
    },
    {
      id: 'services',
      title: TEXT('Services')
    },
    {
      id: 'volumes',
      title: TEXT('Volumes')
    },
    {
      id: 'sysInfo',
      title: TEXT('System Information')
    },
    {
      id: 'hosts',
      title: TEXT('Hosts')
    }
  ];

  constructor(private localStorageService: LocalStorageService) {}

  ngOnInit(): void {
    const value = this.localStorageService.get('dashboard_widgets');
    if (_.isString(value)) {
      this.enabled = JSON.parse(value);
    }
  }

  onToggleWidget(id: string) {
    if (this.enabled.includes(id)) {
      _.pull(this.enabled, id);
    } else {
      this.enabled.push(id);
    }
    this.localStorageService.set('dashboard_widgets', JSON.stringify(this.enabled));
  }

  get enabledWidgets() {
    return _.filter(this.widgets, (widget) => this.enabled.includes(widget.id));
  }
}
