import { useState, useMemo, useCallback } from 'react';
import { useStore, useDispatch } from '@hooks';
import { getUsers } from '@store/adcm/users/usersSlice';
import { createGroup } from '@store/adcm/groups/groupActionsSlice';
import { AdcmGroupUserPayload } from '@models/adcm';

interface CreateGroupFormData {
  name: string;
  description: string;
  usersIds: number[];
}

const initialFormData: CreateGroupFormData = {
  name: '',
  description: '',
  usersIds: [],
};

export const useCreateGgoupForm = () => {
  const dispatch = useDispatch();

  const users = useStore(({ adcm }) => adcm.users.users);

  const usersOptions = useMemo(() => {
    return users.map(({ username, id }) => ({ value: id, label: username }));
  }, [users]);

  const [formData, setFormData] = useState<CreateGroupFormData>(initialFormData);

  const isValid = useMemo(() => {
    const { usersIds } = formData;
    return usersIds.length > 0;
  }, [formData]);

  const resetForm = useCallback(() => {
    setFormData(initialFormData);
  }, []);

  const submitForm = useCallback(() => {
    const { usersIds, description, name } = formData;
    if (usersIds.length > 0) {
      dispatch(
        createGroup({
          name,
          displayName: name,
          description,
          users: usersIds,
        }),
      );
    }
  }, [formData, dispatch]);

  const loadRelatedData = useCallback(() => {
    dispatch(getUsers());
  }, [dispatch]);

  const handleChangeFormData = (changes: Partial<CreateGroupFormData>) => {
    setFormData({
      ...formData,
      ...changes,
    });
  };

  return {
    isValid,
    formData,
    resetForm,
    submitForm,
    onChangeFormData: handleChangeFormData,
    loadRelatedData,
    relatedData: {
      usersOptions,
    },
  };
};
