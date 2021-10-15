import { Component } from '@angular/core';

import { DetailComponent } from '@app/shared/details/detail.component';
import { LeftMenuItem } from '@app/shared/details/left-menu/left-menu.component';
import { DetailsFactory } from '@app/factories/details.factory';

@Component({
  selector: 'app-host-details',
  templateUrl: '../../../templates/details.html',
  styleUrls: ['./../../../shared/details/detail.component.scss']
})
export class HostDetailsComponent extends DetailComponent {

  leftMenu: LeftMenuItem[] = [
    DetailsFactory.labelMenuItem('Main', 'main'),
    DetailsFactory.labelMenuItem('Configuration', 'config'),
    DetailsFactory.statusMenuItem('Status', 'status'),
  ];

}
