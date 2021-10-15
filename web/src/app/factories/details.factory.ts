import { LeftMenuItem } from '../shared/details/left-menu/left-menu.component';
import { LabelMenuItemComponent } from '../shared/details/label-menu-item/label-menu-item.component';
import { StatusMenuItemComponent } from '@app/shared/details/status-menu-item/status-menu-item.component';

export class DetailsFactory {

  static labelMenuItem(label: string, link: string): LeftMenuItem {
    return {
      label,
      link,
      component: LabelMenuItemComponent,
    };
  }

  static statusMenuItem(label: string, link: string): LeftMenuItem {
    return {
      label,
      link,
      component: StatusMenuItemComponent,
    };
  }

}
