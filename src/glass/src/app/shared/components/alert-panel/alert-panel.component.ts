/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Component, Input } from '@angular/core';

@Component({
  selector: 'glass-alert-panel',
  templateUrl: './alert-panel.component.html',
  styleUrls: ['./alert-panel.component.scss']
})
export class AlertPanelComponent {
  @Input()
  type: 'success' | 'info' | 'warning' | 'error' | 'hint' = 'error';

  // https://suse.eosdesignsystem.com/alerts/global
  iconMap: Record<string, string> = {
    success: 'mdi:check',
    info: 'mdi:information-outline',
    warning: 'mdi:alert-outline',
    error: 'mdi:alert-circle-outline',
    hint: 'mdi:lightbulb-on-outline'
  };
}
