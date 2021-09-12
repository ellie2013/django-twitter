class HBaseField:
    field_type = None

    def __init__(self, reverse=False, column_family=None):
        self.reverse = reverse
        self.column_family = column_family
        # <HOMEWORK>
        # 增加 is_required 属性，默认为 true 和 default 属性，默认 None。
        # 并在 HbaseModel 中做相应的处理，抛出相应的异常信息


class IntegerField(HBaseField):
    field_type = 'int'
    # 以下这个__int__ 也可以不用写，因为子类跟父类一样，子类的__int__没有做任何改变
    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)


class TimestampField(HBaseField):
    field_type = 'timestamp'
    # 以下这个__int__ 也可以不用写，因为子类跟父类一样，子类的__int__没有做任何改变
    def __init__(self, *args, auto_now_add=False, **kwargs):
        super(TimestampField, self).__init__( *args, **kwargs)