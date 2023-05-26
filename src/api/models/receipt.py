class receipt:
    def __init__(self, abn, date, file_name, merchant_name, merchant_phone, payer, payment_method, payment_status, receipt_no, share_with, time, total):
        # no id at the moment
        self.abn = abn
        self.date = date
        self.file_name = file_name
        self.merchant_name = merchant_name
        self.merchant_phone = merchant_phone
        self.payer = payer
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.receipt_no = receipt_no
        # list of user names
        self.share_with = share_with
        self.time = time
        self.total = total

    def __repr__(self):
        return f"<receipt {self.id}>"

    def serialize(self):
        return {
            "abn": self.abn,
            "date": self.date,
            "file_name": self.file_name,
            "merchant_name": self.merchant_name,
            "merchant_phone": self.merchant_phone,
            "payer": self.payer,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "receipt_no": self.receipt_no,
            "share_with": self.share_with,
            "time": self.time,
            "total": self.total
        }
