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
import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DeclarativeFormComponent } from '~/app/shared/components/declarative-form/declarative-form.component';
import {
  DeclarativeFormConfig,
  FormFieldConfig
} from '~/app/shared/models/declarative-form-config.type';
import { Interface, NetworkService } from '~/app/shared/services/api/network.service';

@Component({
  selector: 'glass-network-form',
  templateUrl: './network-form.component.html',
  styleUrls: ['./network-form.component.scss']
})
export class NetworkFormComponent implements OnInit {
  @ViewChild(DeclarativeFormComponent, { static: false })
  form!: DeclarativeFormComponent;

  @BlockUI()
  blockUI!: NgBlockUI;

  pageStatus: PageStatus = PageStatus.none;
  fields: { [fieldName: string]: FormFieldConfig } = {
    name: {
      type: 'text',
      label: TEXT('Name'),
      name: 'name',
      readonly: true
    },
    type: {
      type: 'select',
      name: 'type',
      label: TEXT('Type'),
      options: {
        dhcp: TEXT('DHCP'),
        static: TEXT('Static')
      }
    },
    address: {
      type: 'text',
      label: TEXT('IP Address'),
      name: 'addr',
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
    netmask: {
      type: 'text',
      label: TEXT('Netmask'),
      name: 'netmask',
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
    gateway: {
      type: 'text',
      label: TEXT('Gateway'),
      name: 'gateway',
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
  };
  // @ts-ignore
  // formConfig won't be used before declaration through the use of ngIf in template.
  formConfig: DeclarativeFormConfig;

  constructor(
    private route: ActivatedRoute,
    private networkService: NetworkService,
    private router: Router
  ) {
    this.route.params.subscribe((p: { name?: string }) => {
      this.pageStatus = PageStatus.loading;
      this.networkService.get(p.name!).subscribe(
        (network) => {
          this.pageStatus = PageStatus.ready;
          this.edit(network);
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
    });
  }

  ngOnInit(): void {}

  edit(networkInterface: Interface) {
    this.fields.name.value = networkInterface.name;
    this.fields.type.value = networkInterface.config.bootproto;
    this.fields.address.value = networkInterface.config.addr;
    this.fields.netmask.value = networkInterface.config.netmask;
    this.fields.gateway.value = networkInterface.config.gateway;

    const edit = TEXT('Edit');
    this.setFormConfig(`${edit} ${networkInterface.name}`, edit, () =>
      this.interfaceAction('update', TEXT('Please wait, updating interface ...'))
    );
  }

  private setFormConfig(title: string, submitButtonText: string, submitFn: () => void) {
    this.formConfig = {
      buttons: [
        {
          type: 'default',
          text: TEXT('Cancel'),
          click: () => this.router.navigate(['dashboard/network'])
        },
        { type: 'submit', text: submitButtonText, click: submitFn }
      ],
      fields: [
        this.fields.name,
        this.fields.type,
        this.fields.address,
        this.fields.netmask,
        this.fields.gateway
      ],
      title
    };
  }

  private interfaceAction(actionName: 'update', startText: string) {
    this.blockUI.start(startText);
    const action = this.networkService[actionName](this.getInterface()) as Observable<any>;
    action
      .pipe(finalize(() => this.blockUI.stop()))
      .subscribe(() => this.router.navigate(['dashboard/network']));
  }

  private getInterface(): Interface {
    return this.form.values as Interface;
  }
}
