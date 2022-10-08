func (s *KasadaSolver) FetchKasadaUnicorn() error {

    u := `https://us.unicorn-bot.com/api/kpsdk/ips/?kpver=v20210513&host=https%3A%2F%2Fmobile.api.prod.veve.me&site=VEVE&compress_method=GZIP`

    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)
    fw, err := writer.CreateFormFile("ips_js", "ips_js")
    if err != nil {
        return err
    }
    var b bytes.Buffer
    w := gzip.NewWriter(&b)
    w.Write([]byte(s.rawIpBody))
    w.Close()

    io.Copy(fw, bytes.NewReader(b.Bytes()))
    writer.Close()

    headers := map[string][]string{
        "Authorization": {"Bearer " + s.ApiKey},
        "content-type":  {writer.FormDataContentType()},
    }
    ordered := []string{
        "Authorization",
        "content-type",
        "Cookie",
    }

    return s.DoAct(task.Action{
        Client:         s.normalClient,
        Request:        s.MakeReq(u, headers, ordered, "POST", body.Bytes()),
        Label:          "Fetch Kasada Solve",
        ValidRespCodes: []int{200},
        HideHTTPError:  true,
        BodyHandler: func(b []byte) error {
            var r UnicornKasadaResponse

            if err := json.Unmarshal(b, &r); err != nil {
                return err
            }

            decoded, err := base64.StdEncoding.DecodeString(r.TlBodyB64)
            if err != nil {
                return err
            }
            reader, err := gzip.NewReader(bytes.NewReader(decoded))
            if err != nil {
                return err
            }

            bb, _ := ioutil.ReadAll(reader)

            s.solveData = bb

            return nil
        },
    })
}
