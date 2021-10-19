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
import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { translate } from '~/app/i18n.helper';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';
import { Interface, NetworkService } from '~/app/shared/services/api/network.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-network-page',
  templateUrl: './network-page.component.html',
  styleUrls: ['./network-page.component.scss']
})
export class NetworkPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  loading = false;
  firstLoadComplete = false;
  data: Interface[] = [];
  columns: DatatableColumn[];

  constructor(private dialogService: DialogService, private networkService: NetworkService) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'name'
      },
      {
        name: TEXT('Address'),
        prop: 'config.addr'
      },
      {
        name: TEXT('Type'),
        prop: 'config.bootproto',
        cellTemplateName: DatatableCellTemplateName.map,
        cellTemplateConfig: {
          dhcp: TEXT('DHCP'),
          static: TEXT('Static')
        }
      },
      {
        name: TEXT('Enabled'),
        prop: 'config.enabled',
        cellTemplateName: DatatableCellTemplateName.checkIcon
      },
      {
        name: '',
        prop: '',
        unsortable: true,
        cellTemplateName: DatatableCellTemplateName.actionMenu,
        cellTemplateConfig: this.onActionMenu.bind(this)
      }
    ];
  }

  loadData(): void {
    this.loading = true;
    this.networkService.interfaces().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
  }

  onActionMenu(selected: Interface): DatatableActionItem[] {
    const result: DatatableActionItem[] = [
      {
        title: TEXT('Edit'),
        callback: (data: DatatableData) => {
          this.dialogService.open(
            DeclarativeFormModalComponent,
            (res: Interface | boolean) => {
              if (res) {
                this.blockUI.start(translate(TEXT('Please wait, updating interface ...')));
                //this.networkService
                //  .update(UPDATE THE NETWORK INTERFACE)
                //  .pipe(finalize(() => this.blockUI.stop()))
                //  .subscribe(() => {
                //    this.loadData();
                //  });
                this.blockUI.stop();
              }
            },
            {
              title: TEXT('Edit Interface'),
              formConfig: {
                fields: [
                  {
                    type: 'text',
                    label: TEXT('Name'),
                    name: 'name',
                    value: selected.name,
                    readonly: true
                  },
                  {
                    type: 'select',
                    name: 'type',
                    label: TEXT('Type'),
                    value: selected.config.bootproto,
                    options: {
                      dhcp: TEXT('DHCP'),
                      static: TEXT('Static')
                    }
                  },
                  {
                    type: 'text',
                    label: TEXT('IP Address'),
                    name: 'addr',
                    value: selected.config.addr,
                    validators: {
                      patternType: 'hostAddress',
                      requiredIf: {
                        operator: 'eq',
                        arg0: { prop: 'type' },
                        arg1: 'static'
                      }
                    },
                    modifiers: [
                      {
                        type: 'readonly',
                        constraint: {
                          operator: 'eq',
                          arg0: { prop: 'type' },
                          arg1: 'dhcp'
                        }
                      }
                    ]
                  },
                  {
                    type: 'text',
                    label: TEXT('Netmask'),
                    name: 'netmask',
                    value: selected.config.netmask,
                    validators: {
                      patternType: 'hostAddress',
                      requiredIf: {
                        operator: 'eq',
                        arg0: { prop: 'type' },
                        arg1: 'static'
                      }
                    },
                    modifiers: [
                      {
                        type: 'readonly',
                        constraint: {
                          operator: 'eq',
                          arg0: { prop: 'type' },
                          arg1: 'dhcp'
                        }
                      }
                    ]
                  },
                  {
                    type: 'text',
                    label: TEXT('Gateway'),
                    name: 'gateway',
                    value: selected.config.gateway,
                    validators: {
                      patternType: 'hostAddress',
                      requiredIf: {
                        operator: 'eq',
                        arg0: { prop: 'type' },
                        arg1: 'static'
                      }
                    },
                    modifiers: [
                      {
                        type: 'readonly',
                        constraint: {
                          operator: 'eq',
                          arg0: { prop: 'type' },
                          arg1: 'dhcp'
                        }
                      }
                    ]
                  }
                ]
              }
            }
          );
        }
      }
    ];
    return result;
  }
}
