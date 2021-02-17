/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { VolumesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/volumes-dashboard-widget/volumes-dashboard-widget.component';
import { OrchService, Volume } from '~/app/shared/services/api/orch.service';

describe('DevicesDashboardWidgetComponent', () => {
  let component: VolumesDashboardWidgetComponent;
  let fixture: ComponentFixture<VolumesDashboardWidgetComponent>;
  const mockedVolumes: Volume[] = [
    {
      available: true,
      device_id: '01123456',
      human_readable_type: 'hdd',
      lsm_data: {},
      lvs: [],
      path: '/dev/vdb',
      rejected_reasons: [],
      sys_api: {
        human_readable_size: '8.00 GB',
        locked: 0,
        model: '',
        nr_requests: 256,
        partitions: {},
        removable: false,
        rev: '',
        ro: false,
        rotational: true,
        sas_address: '',
        sas_device_handle: '',
        scheduler_mode: 'mq-deadline',
        sectors: 0,
        sectorsize: 512,
        size: 8589934592,
        support_discard: 0,
        vendor: '0x1af4'
      }
    },
    {
      available: true,
      device_id: '01789101',
      human_readable_type: 'hdd',
      lsm_data: {},
      lvs: [],
      path: '/dev/vdc',
      rejected_reasons: [],
      sys_api: {
        human_readable_size: '8.00 GB',
        locked: 0,
        model: '',
        nr_requests: 256,
        partitions: {},
        removable: false,
        rev: '',
        ro: false,
        rotational: true,
        sas_address: '',
        sas_device_handle: '',
        scheduler_mode: 'mq-deadline',
        sectors: 0,
        sectorsize: 512,
        size: 8589934592,
        support_discard: 0,
        vendor: '0x1af4'
      }
    },
    {
      available: true,
      device_id: '01112131',
      human_readable_type: 'hdd',
      lsm_data: {},
      lvs: [],
      path: '/dev/vdd',
      rejected_reasons: [],
      sys_api: {
        human_readable_size: '8.00 GB',
        locked: 0,
        model: '',
        nr_requests: 256,
        partitions: {},
        removable: false,
        rev: '',
        ro: false,
        rotational: true,
        sas_address: '',
        sas_device_handle: '',
        scheduler_mode: 'mq-deadline',
        sectors: 0,
        sectorsize: 512,
        size: 8589934592,
        support_discard: 0,
        vendor: '0x1af4'
      }
    },
    {
      available: true,
      device_id: '01415161',
      human_readable_type: 'hdd',
      lsm_data: {},
      lvs: [],
      path: '/dev/vde',
      rejected_reasons: [],
      sys_api: {
        human_readable_size: '8.00 GB',
        locked: 0,
        model: '',
        nr_requests: 256,
        partitions: {},
        removable: false,
        rev: '',
        ro: false,
        rotational: true,
        sas_address: '',
        sas_device_handle: '',
        scheduler_mode: 'mq-deadline',
        sectors: 0,
        sectorsize: 512,
        size: 8589934592,
        support_discard: 0,
        vendor: '0x1af4'
      }
    },
    {
      available: false,
      device_id: '',
      human_readable_type: 'hdd',
      lsm_data: {},
      lvs: [],
      path: '/dev/vda',
      rejected_reasons: ['locked'],
      sys_api: {
        human_readable_size: '24.00 GB',
        locked: 1,
        model: '',
        nr_requests: 256,
        partitions: {
          vda4: {
            start: '39827456',
            sectors: '10504159',
            sectorsize: 512,
            size: 5378129408,
            human_readable_size: '5.01 GB',
            holders: []
          },
          vda2: {
            start: '6144',
            sectors: '40960',
            sectorsize: 512,
            size: 20971520,
            human_readable_size: '20.00 MB',
            holders: []
          },
          vda3: {
            start: '47104',
            sectors: '39780352',
            sectorsize: 512,
            size: 20367540224,
            human_readable_size: '18.97 GB',
            holders: []
          },
          vda1: {
            start: '2048',
            sectors: '4096',
            sectorsize: 512,
            size: 2097152,
            human_readable_size: '2.00 MB',
            holders: []
          }
        },
        removable: false,
        rev: '',
        ro: false,
        rotational: true,
        sas_address: '',
        sas_device_handle: '',
        scheduler_mode: 'mq-deadline',
        sectors: 0,
        sectorsize: 512,
        size: 25769803776,
        support_discard: 0,
        vendor: '0x1af4'
      }
    }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule, HttpClientTestingModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(VolumesDashboardWidgetComponent);
    component = fixture.componentInstance;
    spyOn(TestBed.inject(OrchService), 'volumes').and.returnValue(of(mockedVolumes));
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should filter out not available devices', (done) => {
    component.loadData().subscribe((x) => {
      expect(x.length > 0).toBe(true);
      done();
    });
  });
});
